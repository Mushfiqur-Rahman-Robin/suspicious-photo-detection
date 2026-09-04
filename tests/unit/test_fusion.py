"""Unit tests: signal fusion (SPEC §10.4, ED-4, P2.4)."""

from __future__ import annotations

import numpy as np
import pytest

from core.exceptions import DetectionError
from scoring.fusion import fused_suspicion_scores


def test_equal_weights_fuse_simply():
    scores = fused_suspicion_scores(
        np.array([0.1, 0.9]),
        np.array([0.1, 0.9]),
        np.array([0.1, 0.9]),
        centroid_weight=1 / 3,
        knn_weight=1 / 3,
        isolation_forest_weight=1 / 3,
        image_count=20,
        min_images_for_isolation_forest=10,
    )
    np.testing.assert_allclose(scores, np.array([0.1, 0.9]))


def test_results_are_clamped_to_unit_interval():
    scores = fused_suspicion_scores(
        np.array([2.0, -1.0]),
        np.array([0.0, 0.0]),
        None,
        centroid_weight=0.5,
        knn_weight=0.5,
        isolation_forest_weight=0.0,
        image_count=3,
        min_images_for_isolation_forest=10,
    )
    assert scores[0] == 1.0
    assert scores[1] == 0.0


def test_if_weight_is_reduced_for_small_outlets():
    big = fused_suspicion_scores(
        np.array([1.0]),
        np.array([0.0]),
        np.array([1.0]),
        1 / 3,
        1 / 3,
        1 / 3,
        image_count=20,
        min_images_for_isolation_forest=10,
    )
    small = fused_suspicion_scores(
        np.array([1.0]),
        np.array([0.0]),
        np.array([1.0]),
        1 / 3,
        1 / 3,
        1 / 3,
        image_count=5,
        min_images_for_isolation_forest=10,
    )
    assert float(big[0]) > float(small[0])  # IF contributes less at small N


def test_missing_if_renormalizes_remaining_weights():
    scores = fused_suspicion_scores(
        np.array([1.0]),
        np.array([0.0]),
        None,
        centroid_weight=0.5,
        knn_weight=0.5,
        isolation_forest_weight=0.0,
        image_count=2,
        min_images_for_isolation_forest=10,
    )
    assert scores[0] == pytest.approx(0.5)


def test_shape_mismatch_raises():
    with pytest.raises(DetectionError):
        fused_suspicion_scores(
            np.array([1.0]),
            np.array([1.0]),
            np.array([1.0, 1.0]),
            1 / 3,
            1 / 3,
            1 / 3,
            5,
            10,
        )
