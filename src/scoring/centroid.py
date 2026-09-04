"""Robust centroid distance signal (SPEC §10.3, ED-3).

The outlet's reference appearance is the coordinate-wise median of its
L2-normalized embeddings (re-normalized) rather than the mean, so a single
injected fake cannot drag the reference toward itself (breakdown resistance).
"""

from __future__ import annotations

import numpy as np


def robust_centroid(embeddings: np.ndarray) -> np.ndarray:
    """Return the re-normalized coordinate-wise median of the embeddings.

    A zero-norm median (numerically degenerate) is returned as-is so callers
    never divide by zero; the centroid-distance signal then degrades
    gracefully instead of producing NaN.
    """
    centroid = np.asarray(np.median(embeddings, axis=0))
    norm = np.linalg.norm(centroid)
    if norm == 0.0:
        return centroid
    return np.asarray(centroid / norm)


def centroid_distances(embeddings: np.ndarray, centroid: np.ndarray) -> np.ndarray:
    """Per-image centroid signal: ``1 - cosine(e_i, centroid)``.

    Values are 0 for an image exactly at the outlet's typical appearance and
    grow toward 2 for anti-correlated ones (SPEC §12 direction: higher = more
    anomalous); downstream fusion clamps to [0, 1].
    """
    return np.asarray(1.0 - embeddings @ centroid)
