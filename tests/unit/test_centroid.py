"""Unit tests: robust centroid signal (SPEC §10.3, ED-3, P2.2)."""

from __future__ import annotations

import numpy as np
import pytest

from embedding.normalize import l2_normalize
from scoring.centroid import centroid_distances, robust_centroid


def test_centroid_of_identical_vectors_is_that_vector():
    vectors = l2_normalize(np.tile(np.array([1.0, 0.0]), (5, 1)))
    centroid = robust_centroid(vectors)
    np.testing.assert_allclose(centroid, np.array([1.0, 0.0]), atol=1e-9)


def test_centroid_is_renormalized():
    rng = np.random.default_rng(1)
    vectors = l2_normalize(rng.normal(size=(7, 4)))
    centroid = robust_centroid(vectors)
    assert np.linalg.norm(centroid) == pytest.approx(1.0)


def test_median_is_robust_to_an_outlier():
    rng = np.random.default_rng(2)
    dim = 16
    base_x = l2_normalize(rng.normal(size=(1, dim)))[0]
    base_y = l2_normalize(rng.normal(size=(1, dim)))[0]
    while abs(float(base_x @ base_y)) > 0.2:
        base_y = l2_normalize(rng.normal(size=(1, dim)))[0]

    cluster = l2_normalize(base_x + rng.normal(scale=0.05, size=(4, dim)))
    outlier = l2_normalize(base_y + rng.normal(scale=0.05, size=(1, dim)))
    vectors = np.vstack([cluster, outlier])

    clean_median = robust_centroid(cluster)
    contaminated_median = robust_centroid(vectors)
    clean_mean = l2_normalize(cluster.mean(axis=0)[None, :])[0]
    contaminated_mean = l2_normalize(vectors.mean(axis=0)[None, :])[0]

    # the median centroid is far less perturbed by the single outlier than the mean
    median_shift = float(1.0 - clean_median @ contaminated_median)
    mean_shift = float(1.0 - clean_mean @ contaminated_mean)
    assert median_shift < mean_shift
    assert median_shift < 0.01


def test_centroid_distance_is_zero_for_identical_images():
    vectors = l2_normalize(np.tile(np.array([1.0, 0.0]), (3, 1)))
    distances = centroid_distances(vectors, robust_centroid(vectors))
    np.testing.assert_allclose(distances, np.zeros(3), atol=1e-9)


def test_centroid_distance_direction_is_higher_more_anomalous():
    vectors = np.array([[1.0, 0.0], [0.0, 1.0]])
    centroid = robust_centroid(vectors)
    distances = centroid_distances(vectors, centroid)
    assert distances[0] == pytest.approx(distances[1])
    assert 0.0 <= float(np.min(distances)) <= float(np.max(distances)) <= 2.0


def test_zero_norm_median_returns_zeros():
    vectors = np.zeros((3, 4))
    centroid = robust_centroid(vectors)
    np.testing.assert_allclose(centroid, np.zeros(4))
