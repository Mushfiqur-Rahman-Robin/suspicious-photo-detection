"""Unit tests: reason templates (SPEC §11.4, FR5, P3.4)."""

from __future__ import annotations

from detection.reasons import (
    COMBINED_CENTROID_KNN_REASON,
    REASON_BY_DOMINANT,
    reason_for_signals,
)


def _reasons(**kwargs):
    defaults = {
        "centroid_distance": 0.9,
        "knn_consensus": 0.1,
        "isolation_forest": None,
        "centroid_weight": 1 / 3,
        "knn_weight": 1 / 3,
        "isolation_forest_weight": 1 / 3,
    }
    defaults.update(kwargs)
    return reason_for_signals(**defaults)


def test_centroid_dominant_reason():
    assert (
        _reasons(centroid_distance=0.9, knn_consensus=0.1)
        == REASON_BY_DOMINANT["centroid"]
    )


def test_knn_dominant_reason():
    assert (
        _reasons(centroid_distance=0.1, knn_consensus=0.9) == REASON_BY_DOMINANT["knn"]
    )


def test_if_dominant_reason():
    assert (
        _reasons(
            centroid_distance=0.1,
            knn_consensus=0.1,
            isolation_forest=0.9,
        )
        == REASON_BY_DOMINANT["isolation_forest"]
    )


def test_combined_centroid_and_knn_reason():
    assert (
        _reasons(centroid_distance=0.8, knn_consensus=0.8, isolation_forest=0.1)
        == COMBINED_CENTROID_KNN_REASON
    )


def test_combined_template_wins_when_close_but_knn_second():
    assert (
        _reasons(centroid_distance=0.800001, knn_consensus=0.8, isolation_forest=None)
        == COMBINED_CENTROID_KNN_REASON
    )


def test_all_templates_are_nonempty_and_distinct():
    assert len(set(REASON_BY_DOMINANT.values())) == len(REASON_BY_DOMINANT)
    assert all(len(value) > 5 for value in REASON_BY_DOMINANT.values())


def test_combined_reason_matches_prd_example_wording():
    assert COMBINED_CENTROID_KNN_REASON == (
        "Distinct background and signage compared to the rest of the series"
    )
