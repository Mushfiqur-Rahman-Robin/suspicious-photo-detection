"""Unit tests: synthetic-golden evaluation (SPEC §16, §21; P5.1)."""

from __future__ import annotations

import numpy as np

from config.settings import Settings
from detection.ensemble_detector import EnsembleDetector
from reporting.evaluation import (
    DetectionMetrics,
    build_scenarios,
    compose_evaluation_report,
    compute_metrics,
    run_evaluation,
)


def test_metrics_perfect_detection():
    metrics = compute_metrics({"a.jpg", "b.jpg"}, {"a.jpg", "b.jpg"})
    assert metrics.true_positives == 2
    assert metrics.false_positives == 0
    assert metrics.false_negatives == 0
    assert metrics.precision == 1.0
    assert metrics.recall == 1.0
    assert metrics.f1 == 1.0


def test_metrics_with_false_positive_and_false_negative():
    metrics = compute_metrics({"a.jpg", "c.jpg"}, {"a.jpg", "b.jpg"})
    assert metrics.true_positives == 1
    assert metrics.false_positives == 1
    assert metrics.false_negatives == 1
    assert metrics.precision == 0.5
    assert metrics.recall == 0.5
    assert metrics.f1 == 0.5


def test_metrics_no_positive_ground_truth():
    clean = compute_metrics(set(), set())
    assert clean.precision == 1.0
    assert clean.recall == 1.0
    assert clean.f1 == 1.0
    over_flagged = compute_metrics({"a.jpg"}, set())
    assert over_flagged.precision == 0.0
    assert over_flagged.recall == 1.0


def test_metrics_missed_fake_is_not_masked_as_perfect():
    missed = compute_metrics(set(), {"a.jpg"})
    assert missed.true_positives == 0
    assert missed.false_negatives == 1
    assert missed.recall == 0.0
    assert missed.f1 == 0.0


def test_scenarios_are_deterministic():
    first = build_scenarios(random_seed=42)
    second = build_scenarios(random_seed=42)
    assert [scenario.name for scenario in first] == [
        scenario.name for scenario in second
    ]
    for left, right in zip(first, second, strict=True):
        np.testing.assert_array_equal(left.embeddings, right.embeddings)
        assert left.file_names == right.file_names
        assert left.ground_truth == right.ground_truth


def test_scenario_covers_required_failure_modes():
    scenarios = {
        scenario.name: scenario for scenario in build_scenarios(random_seed=42)
    }
    assert {
        "single_fake",
        "tight_clique",
        "multi_cluster_legit",
        "uniform_outlet",
        "small_outlet",
    } <= set(scenarios)
    assert scenarios["single_fake"].ground_truth == {"unrelated_shot.jpg"}
    assert scenarios["multi_cluster_legit"].ground_truth == set()


def test_run_evaluation_all_scenarios_pass_gates():
    settings = Settings()
    detector = EnsembleDetector(settings)
    metrics = run_evaluation(detector, settings)
    for scenario_metrics in metrics.values():
        assert scenario_metrics.precision >= settings.golden_min_precision
        assert scenario_metrics.recall >= settings.golden_min_recall
        assert scenario_metrics.f1 >= settings.golden_min_f1


def test_evaluation_report_contains_table_and_verdict():
    settings = Settings()
    metrics = {
        name: DetectionMetrics(1, 0, 0, 1.0, 1.0, 1.0)
        for name in ["single_fake", "multi_cluster_legit"]
    }
    report = compose_evaluation_report(metrics, settings)
    assert "| Scenario | TP | FP | FN |" in report
    assert "single_fake" in report
    assert "All scenarios pass" in report


def test_evaluation_report_flags_failures():
    settings = Settings()
    metrics = {"single_fake": DetectionMetrics(0, 1, 1, 0.0, 0.0, 0.0)}
    report = compose_evaluation_report(metrics, settings)
    assert "FAIL" in report
    assert "At least one scenario fails" in report
