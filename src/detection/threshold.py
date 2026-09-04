"""Adaptive, per-outlet flag threshold (SPEC §11.1, ED-5).

``tau = max(median(scores) + k * MAD(scores), SCORE_FLOOR)`` with MAD scaled
by 1.4826 for a normal-consistent estimator. The threshold is distribution
free, outlier resistant, and per outlet - a global threshold would be wrong
because outlet appearance variance differs wildly across outlets.
"""

from __future__ import annotations

import numpy as np

MAD_SCALE = 1.4826


def median_absolute_deviation(scores: np.ndarray) -> float:
    """Scaled MAD of ``scores`` (normal-consistent estimator, SPEC §11.1)."""
    median = float(np.median(scores))
    return float(MAD_SCALE * np.median(np.abs(scores - median)))


def adaptive_flag_threshold(
    scores: np.ndarray,
    mad_k: float,
    score_floor: float,
) -> float:
    """Compute the per-outlet flag threshold.

    An empty score vector yields the floor; otherwise the threshold is the
    median plus ``mad_k`` scaled MADs, never below the absolute floor so a
    near-uniform outlet is not over-flagged by noise (SPEC §11.2).
    """
    if scores.size == 0:
        return score_floor
    median = float(np.median(scores))
    return max(median + mad_k * median_absolute_deviation(scores), score_floor)
