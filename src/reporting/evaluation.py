"""Synthetic-golden quality evaluation (SPEC §16, §21; TASKS P5.1).

The real dataset has no labels, so precision/recall/F1 can only be measured
on synthetic outlets with known injected outliers. Embeddings are generated
deterministically (fixed seed) as tight unit-sphere clusters plus injected
far-away points, then run through the configured detector; the flagged set is
compared to ground truth. Scenarios cover the PRD failure modes: a single
unrelated image, a tight clique of fakes, a legitimate second cluster, a
near-uniform outlet, and a small outlet.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from config.settings import Settings
from core.ports import OutlierDetector
from embedding.normalize import l2_normalize

SCENARIO_EMBEDDING_DIM = 64
CLUSTER_SPREAD = 0.15


@dataclass(frozen=True, slots=True)
class DetectionMetrics:
    """Precision/recall/F1 of flagging on one synthetic scenario."""

    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1: float


@dataclass(frozen=True, slots=True)
class SyntheticScenario:
    """One synthetic outlet: embeddings, names, and the known outlier ground truth."""

    name: str
    embeddings: np.ndarray
    file_names: list[str]
    ground_truth: set[str]


def compute_metrics(flagged: set[str], ground_truth: set[str]) -> DetectionMetrics:
    """Compute precision/recall/F1 of ``flagged`` against ``ground_truth``.

    A missed fake is always a false negative: when the ground truth contains
    positives but none were flagged, recall is 0 (never masked to a perfect
    score). Only a scenario with no expected positives and no flags counts as
    perfect.
    """
    true_positives = len(flagged & ground_truth)
    false_positives = len(flagged - ground_truth)
    false_negatives = len(ground_truth - flagged)
    if true_positives == 0:
        precision = 1.0 if false_positives == 0 else 0.0
        recall = 0.0 if false_negatives > 0 else 1.0
    else:
        precision = true_positives / (true_positives + false_positives)
        recall = true_positives / (true_positives + false_negatives)
    if precision + recall == 0.0:
        f1 = 0.0
    else:
        f1 = 2.0 * precision * recall / (precision + recall)
    return DetectionMetrics(
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        precision=precision,
        recall=recall,
        f1=f1,
    )


def build_scenarios(random_seed: int) -> list[SyntheticScenario]:
    """Generate the deterministic scenario set used for evaluation."""
    rng = np.random.default_rng(random_seed)
    base_x = _random_direction(rng)
    base_y = _random_direction(rng)
    while abs(float((base_x @ base_y.T)[0, 0])) > 0.1:
        base_y = _random_direction(rng)

    consistent_count = 20
    consistent = _cluster(base_x, consistent_count, rng)
    consistent_names = [
        f"consistent_{index:03d}.jpg" for index in range(consistent_count)
    ]

    single_fake = np.vstack([consistent, _cluster(base_y, 1, rng)])
    single_fake_names = [*consistent_names, "unrelated_shot.jpg"]

    clique_count = 3
    clique_fakes = _cluster(base_y, clique_count, rng)
    tight_clique = np.vstack([consistent, clique_fakes])
    tight_clique_names = consistent_names + [
        f"clique_fake_{index:03d}.jpg" for index in range(clique_count)
    ]

    # A legitimate second cluster is distinct but only moderately separated
    # (front-vs-interior framing), so no single image dominates the median
    # centroid (ED-10); a wildly different direction would be the fake case.
    second_base = _direction_at_cosine(base_x, target_cosine=0.6, rng=rng)
    second_cluster = _cluster(second_base, consistent_count, rng)
    multi_cluster = np.vstack([consistent, second_cluster])
    multi_cluster_names = consistent_names + [
        f"interior_{index:03d}.jpg" for index in range(consistent_count)
    ]

    uniform = np.tile(base_x, (12, 1))
    uniform_names = [f"uniform_{index:03d}.jpg" for index in range(12)]

    small_count = 6
    small_consistent = _cluster(base_x, small_count, rng)
    small_outlet = np.vstack([small_consistent, _cluster(base_y, 1, rng)])
    small_names = [f"small_{index:03d}.jpg" for index in range(small_count)] + [
        "small_unrelated.jpg"
    ]

    return [
        SyntheticScenario(
            name="single_fake",
            embeddings=single_fake,
            file_names=single_fake_names,
            ground_truth={"unrelated_shot.jpg"},
        ),
        SyntheticScenario(
            name="tight_clique",
            embeddings=tight_clique,
            file_names=tight_clique_names,
            ground_truth=set(tight_clique_names[-clique_count:]),
        ),
        SyntheticScenario(
            name="multi_cluster_legit",
            embeddings=multi_cluster,
            file_names=multi_cluster_names,
            ground_truth=set(),
        ),
        SyntheticScenario(
            name="uniform_outlet",
            embeddings=uniform,
            file_names=uniform_names,
            ground_truth=set(),
        ),
        SyntheticScenario(
            name="small_outlet",
            embeddings=small_outlet,
            file_names=small_names,
            ground_truth={"small_unrelated.jpg"},
        ),
    ]


def run_evaluation(
    detector: OutlierDetector,
    settings: Settings,
) -> dict[str, DetectionMetrics]:
    """Run every scenario through the detector and return metrics by scenario."""
    metrics_by_scenario: dict[str, DetectionMetrics] = {}
    for scenario in build_scenarios(settings.random_seed):
        outcome = detector.detect(scenario.embeddings, scenario.file_names)
        flagged = {entry.file_name for entry in outcome.flagged}
        metrics_by_scenario[scenario.name] = compute_metrics(
            flagged,
            scenario.ground_truth,
        )
    return metrics_by_scenario


def compose_evaluation_report(
    metrics_by_scenario: dict[str, DetectionMetrics],
    settings: Settings,
) -> str:
    """Compose the ``evaluation.md`` markdown report with the verdict vs gates."""
    header = [
        "# Synthetic-Golden Evaluation",
        "",
        "Method: embeddings generated as tight unit-sphere clusters with known "
        "injected outliers, then flagged by the configured detector. The real "
        "dataset is unlabeled, so these numbers are the only precision/recall/F1 "
        "measure available.",
        "",
        "Test-set strategy: these scenarios are the held-out synthetic TEST set "
        "(SPEC §16). The pipeline trains nothing (pretrained embeddings only, "
        "SPEC §2.2), so the unlabeled real photos need no train/test split. The "
        "set is deterministic from the configured seed; a different seed "
        "(`scripts/run_evaluation.py --seed <n>`) samples a fresh held-out test "
        "set, which is how any parameter tuning must be validated - never on the "
        "seed that gates the release.",
        "",
        "| Scenario | TP | FP | FN | Precision | Recall | F1 |",
        "|---|---|---|---|---|---|---|",
    ]
    rows: list[str] = []
    all_passed = True
    for name, metrics in metrics_by_scenario.items():
        passed = (
            metrics.precision >= settings.golden_min_precision
            and metrics.recall >= settings.golden_min_recall
            and metrics.f1 >= settings.golden_min_f1
        )
        all_passed = all_passed and passed
        status = "PASS" if passed else "FAIL"
        rows.append(
            f"| {name} | {metrics.true_positives} | {metrics.false_positives} | "
            f"{metrics.false_negatives} | {metrics.precision:.2f} | "
            f"{metrics.recall:.2f} | {metrics.f1:.2f} | ({status})"
        )
    verdict = (
        "All scenarios pass the configured gates "
        f"(precision>={settings.golden_min_precision}, "
        f"recall>={settings.golden_min_recall}, f1>={settings.golden_min_f1})."
        if all_passed
        else "At least one scenario fails the configured gates."
    )
    return "\n".join(header + rows + ["", verdict, ""])


def _random_direction(rng: np.random.Generator) -> np.ndarray:
    """Return a random unit vector (as a 1-row matrix) in the scenario space."""
    return l2_normalize(rng.normal(size=(1, SCENARIO_EMBEDDING_DIM)))


def _direction_at_cosine(
    base: np.ndarray,
    target_cosine: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Return a unit direction at a controlled angular distance from ``base``."""
    orthogonal = rng.normal(size=(1, SCENARIO_EMBEDDING_DIM))
    orthogonal -= (orthogonal @ base.T) * base
    orthogonal = l2_normalize(orthogonal)
    sine = (1.0 - target_cosine**2) ** 0.5
    return l2_normalize(target_cosine * base + sine * orthogonal)


def _cluster(
    base: np.ndarray,
    count: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """``count`` unit vectors tightly clustered around ``base``.

    The noise is scaled to a fixed vector magnitude (``CLUSTER_SPREAD``)
    rather than a fixed per-dimension std, so the cluster stays a tight
    spherical cap in any embedding dimension.
    """
    noise = rng.normal(size=(count, base.shape[1]))
    noise_norms = np.linalg.norm(noise, axis=1, keepdims=True)
    noise = noise / noise_norms * CLUSTER_SPREAD
    return l2_normalize(base + noise)
