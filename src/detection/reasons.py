"""Deterministic reason templates for flagged images (SPEC §11.4, FR5).

The reason is chosen by the dominant signal(s) - the weighted signal
contributions are compared, not the raw values - so the explanation always
matches the physics that actually pushed the fused score over the threshold.
"""

from __future__ import annotations

# Relative tolerance: when the two leading contributions are centroid and kNN
# and they are within this fraction of the top contribution, neither clearly
# dominates - the combined template (SPEC §11.4) is the honest description.
COMBINED_SIGNAL_RELATIVE_TOLERANCE = 0.05

REASON_BY_DOMINANT: dict[str, str] = {
    "centroid": "Low similarity to cluster centroid",
    "knn": "Few nearby neighbours in feature space",
    "isolation_forest": "Isolated in feature space (Isolation Forest)",
}

COMBINED_CENTROID_KNN_REASON = (
    "Distinct background and signage compared to the rest of the series"
)


def reason_for_signals(
    centroid_distance: float,
    knn_consensus: float,
    isolation_forest: float | None,
    centroid_weight: float,
    knn_weight: float,
    isolation_forest_weight: float,
) -> str:
    """Return the human-readable reason driven by the dominant signal(s).

    When the two leading contributions are centroid and kNN and they are
    within tolerance, the combined template (SPEC §11.4) is used; otherwise
    the single dominant signal's template wins.
    """
    contributions: list[tuple[str, float]] = [
        ("centroid", centroid_weight * centroid_distance),
        ("knn", knn_weight * knn_consensus),
    ]
    if isolation_forest is not None:
        contributions.append(
            ("isolation_forest", isolation_forest_weight * isolation_forest)
        )
    contributions.sort(key=lambda pair: pair[1], reverse=True)
    top_name, top_value = contributions[0]
    second_name, second_value = contributions[1]
    if {top_name, second_name} == {
        "centroid",
        "knn",
    } and top_value - second_value < COMBINED_SIGNAL_RELATIVE_TOLERANCE * top_value:
        return COMBINED_CENTROID_KNN_REASON
    return REASON_BY_DOMINANT[top_name]
