"""Unit tests: seeded Isolation Forest signal (SPEC §10.3, ED-4/ED-6, P3.1)."""

from __future__ import annotations

import numpy as np
import pytest

from core.exceptions import DetectionError
from detection.isolation_forest import isolation_forest_scores


def test_scores_are_in_unit_interval():
    rng = np.random.default_rng(0)
    embeddings = rng.normal(size=(20, 8))
    scores = isolation_forest_scores(embeddings, random_seed=42, n_estimators=50)
    assert np.all(scores >= 0.0)
    assert np.all(scores <= 1.0)
    assert float(np.min(scores)) == pytest.approx(0.0)  # min-max normalized
    assert float(np.max(scores)) == pytest.approx(1.0)


def test_deterministic_across_calls():
    rng = np.random.default_rng(1)
    embeddings = rng.normal(size=(15, 6))
    first = isolation_forest_scores(embeddings, random_seed=7, n_estimators=40)
    second = isolation_forest_scores(embeddings, random_seed=7, n_estimators=40)
    np.testing.assert_array_equal(first, second)


def test_isolated_point_gets_high_score():
    rng = np.random.default_rng(2)
    cluster = rng.normal(loc=0.0, scale=0.1, size=(15, 8))
    isolated = np.array([5.0] * 8)
    embeddings = np.vstack([cluster, isolated])
    scores = isolation_forest_scores(embeddings, random_seed=3, n_estimators=50)
    assert float(scores[-1]) > 0.5


def test_constant_scores_map_to_neutral():
    embeddings = np.tile(np.array([1.0, 0.0]), (6, 1))
    scores = isolation_forest_scores(embeddings, random_seed=1, n_estimators=30)
    np.testing.assert_allclose(scores, np.full(6, 0.5))


def test_requires_at_least_two_images():
    with pytest.raises(DetectionError):
        isolation_forest_scores(np.ones((1, 4)), random_seed=1, n_estimators=10)
