"""Unit tests: ensemble detector (SPEC §11, ED-4/ED-5/ED-9, P3.2)."""

from __future__ import annotations

import numpy as np
import pytest

from config.settings import Settings
from detection.ensemble_detector import EnsembleDetector
from embedding.normalize import l2_normalize


def _detector(**settings_overrides) -> EnsembleDetector:
    return EnsembleDetector(Settings(**settings_overrides))


def _cluster_embeddings(count: int, dim: int = 16, seed: int = 0, spread: float = 0.1):
    rng = np.random.default_rng(seed)
    base = l2_normalize(rng.normal(size=(1, dim)))
    points = l2_normalize(base + rng.normal(scale=spread, size=(count, dim)))
    return points, base[0]


def _random_direction(dim: int = 16, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return l2_normalize(rng.normal(size=(1, dim)))


def _names(prefix: str, count: int) -> list[str]:
    return [f"{prefix}_{index:03d}.jpg" for index in range(count)]


def test_single_fake_is_flagged_with_reason():
    consistent, _ = _cluster_embeddings(20)
    fake = _random_direction(seed=99)
    embeddings = np.vstack([consistent, fake])
    names = [*_names("img", 20), "unrelated.jpg"]
    outcome = _detector().detect(embeddings, names)
    flagged_names = {entry.file_name for entry in outcome.flagged}
    assert "unrelated.jpg" in flagged_names
    assert all(entry.reason for entry in outcome.flagged)


def test_clean_outlet_has_no_flags():
    consistent, _ = _cluster_embeddings(20)
    outcome = _detector().detect(consistent, _names("img", 20))
    assert outcome.flagged == []


def test_tight_clique_of_fakes_is_flagged():
    consistent, _ = _cluster_embeddings(20)
    rng = np.random.default_rng(5)
    fake_base = l2_normalize(rng.normal(size=(1, 16)))
    clique = l2_normalize(fake_base + rng.normal(scale=0.05, size=(3, 16)))
    embeddings = np.vstack([consistent, clique])
    names = [*_names("img", 20), *_names("fake", 3)]
    outcome = _detector().detect(embeddings, names)
    flagged_names = {entry.file_name for entry in outcome.flagged}
    assert set(_names("fake", 3)) <= flagged_names


def test_legitimate_second_cluster_is_not_flagged():
    cluster_a, _ = _cluster_embeddings(12, seed=1)
    cluster_b, _ = _cluster_embeddings(12, seed=2)
    embeddings = np.vstack([cluster_a, cluster_b])
    names = [*_names("front", 12), *_names("interior", 12)]
    outcome = _detector().detect(embeddings, names)
    assert outcome.flagged == []


def test_uniform_outlet_is_not_flagged():
    embeddings = np.tile(np.array([1.0, 0.0, 0.0]), (12, 1))
    outcome = _detector().detect(embeddings, _names("img", 12))
    assert outcome.flagged == []


def test_small_outlet_uses_no_isolation_forest_and_flags_fake():
    consistent, _ = _cluster_embeddings(4, seed=3)
    fake = np.array([[0.0] * 16])
    fake[0, 1] = 1.0
    embeddings = np.vstack([consistent, fake])
    names = [*_names("img", 4), "small_fake.jpg"]
    outcome = _detector().detect(embeddings, names)
    assert {entry.file_name for entry in outcome.flagged} == {"small_fake.jpg"}


def test_single_image_outlet_returns_empty_flags():
    outcome = _detector().detect(np.array([[1.0, 0.0]]), ["solo.jpg"])
    assert outcome.flagged == []
    assert outcome.ranking == ["solo.jpg"]


def test_outlet_below_min_images_returns_empty_flags():
    embeddings = np.array([[1.0, 0.0], [0.0, 1.0]])
    outcome = _detector(min_images_per_outlet=5).detect(embeddings, ["a.jpg", "b.jpg"])
    assert outcome.flagged == []
    assert outcome.suspicion_scores == [0.0, 0.0]


def test_scores_are_within_unit_interval_and_rounded():
    consistent, _ = _cluster_embeddings(20)
    fake = _random_direction(seed=7)
    embeddings = np.vstack([consistent, fake])
    outcome = _detector().detect(embeddings, [*_names("img", 20), "fake.jpg"])
    assert all(0.0 <= score <= 1.0 for score in outcome.suspicion_scores)
    decimals = 4
    assert all(round(score, decimals) == score for score in outcome.suspicion_scores)


def test_ranking_covers_every_image_and_orders_by_score_desc():
    consistent, _ = _cluster_embeddings(12)
    fake = _random_direction(seed=11)
    embeddings = np.vstack([consistent, fake])
    names = [*_names("img", 12), "fake.jpg"]
    outcome = _detector().detect(embeddings, names)
    assert sorted(outcome.ranking) == sorted(names)
    assert outcome.ranking[0] == "fake.jpg"  # most suspicious first (descending)


def test_ranking_ties_are_broken_deterministically():
    embeddings = np.tile(np.array([1.0, 0.0]), (3, 1))
    outcome = _detector().detect(embeddings, ["b.jpg", "a.jpg", "c.jpg"])
    assert outcome.ranking == ["a.jpg", "b.jpg", "c.jpg"]


def test_deterministic_across_runs():
    consistent, _ = _cluster_embeddings(20, seed=4)
    fake = _random_direction(seed=13)
    embeddings = np.vstack([consistent, fake])
    names = [*_names("img", 20), "fake.jpg"]
    first = _detector().detect(embeddings, names)
    second = _detector().detect(embeddings, names)
    assert [entry.file_name for entry in first.flagged] == [
        entry.file_name for entry in second.flagged
    ]
    assert first.ranking == second.ranking


def test_count_mismatch_raises():
    with pytest.raises(ValueError):
        _detector().detect(np.zeros((3, 4)), ["only_two.jpg", "names.jpg"])
