"""Unit tests: adaptive threshold (SPEC §11.1, ED-5, P3.3)."""

from __future__ import annotations

import numpy as np

from detection.threshold import adaptive_flag_threshold, median_absolute_deviation


def test_mad_is_scaled_median_absolute_deviation():
    scores = np.array([0.0, 0.0, 1.0])
    median = 0.0
    mad = median_absolute_deviation(scores)
    assert mad == 1.4826 * np.median(np.abs(scores - median))


def test_threshold_is_median_plus_k_mad():
    scores = np.array([0.1, 0.2, 0.3, 0.4])
    median = 0.25
    mad = median_absolute_deviation(scores)
    expected = median + 3.0 * mad
    assert adaptive_flag_threshold(scores, 3.0, 0.0) == expected


def test_score_floor_binds_when_median_plus_mad_is_low():
    scores = np.array([0.0, 0.0, 0.0])
    assert adaptive_flag_threshold(scores, 3.0, 0.5) == 0.5


def test_empty_scores_return_floor():
    assert adaptive_flag_threshold(np.array([]), 3.0, 0.4) == 0.4


def test_uniform_scores_threshold_is_median_or_floor():
    scores = np.array([0.7, 0.7, 0.7])
    assert adaptive_flag_threshold(scores, 3.0, 0.5) == 0.7
