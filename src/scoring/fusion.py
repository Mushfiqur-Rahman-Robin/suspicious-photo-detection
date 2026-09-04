"""Signal fusion into one bounded suspicion score (SPEC §10.4, ED-4).

The three complementary signals are combined with configurable weights. For
small outlets the Isolation Forest contribution is scaled toward zero because
its scores are unstable at low N (SPEC §11.3); centroid + kNN then dominate
where they are most reliable. The result is always clamped to [0, 1].
"""

from __future__ import annotations

import numpy as np

from core.exceptions import DetectionError


def _normalized_weights(raw_weights: np.ndarray) -> np.ndarray:
    """Renormalize fusion weights to sum to one, rejecting all-zero inputs.

    A degenerate all-zero weight vector (every configured signal unavailable or
    zero-weighted) would divide 0/0 and leak NaN into the fused scores,
    violating the score-in-[0,1] contract; fail fast with a DetectionError.
    """
    if raw_weights.sum() == 0:
        raise DetectionError(
            "fusion weights are all zero; configure a positive signal weight"
        )
    return np.asarray(raw_weights / raw_weights.sum())


def fused_suspicion_scores(
    centroid_distance: np.ndarray,
    knn_consensus: np.ndarray,
    isolation_forest: np.ndarray | None,
    centroid_weight: float,
    knn_weight: float,
    isolation_forest_weight: float,
    image_count: int,
    min_images_for_isolation_forest: int,
) -> np.ndarray:
    """Fuse the per-image signals into scores clamped to [0, 1].

    When the Isolation Forest signal is unavailable (None, or the outlet is
    too small for it to be trusted) the remaining weights are renormalized so
    the fusion always sums to 1 and stays comparable across outlets.
    """
    if isolation_forest is None:
        weights = _normalized_weights(
            np.array([centroid_weight, knn_weight], dtype=np.float64)
        )
        fused = weights[0] * centroid_distance + weights[1] * knn_consensus
    else:
        if isolation_forest.shape != centroid_distance.shape:
            raise DetectionError("isolation forest signal shape mismatch")
        scale = (
            1.0
            if min_images_for_isolation_forest <= 0
            else min(1.0, image_count / min_images_for_isolation_forest)
        )
        weights = _normalized_weights(
            np.array(
                [centroid_weight, knn_weight, isolation_forest_weight * scale],
                dtype=np.float64,
            )
        )
        fused = (
            weights[0] * centroid_distance
            + weights[1] * knn_consensus
            + weights[2] * isolation_forest
        )
    return np.asarray(np.clip(fused, 0.0, 1.0))
