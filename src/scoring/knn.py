"""kNN-consensus signal (SPEC §10.3, ED-10).

The mean similarity to the k nearest neighbours measures local density, so a
well-populated legitimate second cluster is not penalized the way a global
centroid distance would penalize it. Only true isolates (few close
neighbours) receive a high signal.
"""

from __future__ import annotations

import numpy as np


def knn_consensus(similarity_matrix: np.ndarray, k: int) -> np.ndarray:
    """Return the mean similarity to the k nearest neighbours per image.

    ``k`` is clamped to ``max(1, min(k, N-1))`` so the self-similarity
    (diagonal, excluded as -1.0) can never be selected. For N <= 1 the signal
    is defined as 0.0 (no neighbours exist), which is never flagged.
    """
    image_count = similarity_matrix.shape[0]
    if image_count <= 1:
        return np.zeros(image_count, dtype=similarity_matrix.dtype)
    neighbour_count = max(1, min(k, image_count - 1))
    neighbour_indices = np.argsort(-similarity_matrix, axis=1)[:, :neighbour_count]
    neighbour_values = np.take_along_axis(
        similarity_matrix,
        neighbour_indices,
        axis=1,
    )
    return neighbour_values.mean(axis=1)


def knn_signal(similarity_matrix: np.ndarray, k: int) -> np.ndarray:
    """Return the kNN suspicion signal ``1 - mean_top_k_similarity``.

    Higher = fewer/more distant neighbours = more anomalous (SPEC §12).
    """
    return 1.0 - knn_consensus(similarity_matrix, k)
