"""Ensemble outlier detector (SPEC §11, ED-4/ED-5/ED-9).

The detector composes the scoring signals (centroid distance, kNN consensus,
Isolation Forest) with the fusion and the adaptive threshold, then attaches a
deterministic reason to every flagged image and produces the outlet ranking.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from config.settings import Settings
from core.entities import DetectionOutcome
from core.output_schema import FlaggedImage
from detection.isolation_forest import isolation_forest_scores
from detection.reasons import reason_for_signals
from detection.threshold import adaptive_flag_threshold
from observability.logging import get_logger
from scoring.centroid import centroid_distances, robust_centroid
from scoring.fusion import fused_suspicion_scores
from scoring.knn import knn_signal
from scoring.similarity import cosine_similarity_matrix


class EnsembleDetector:
    """Fuses three signals and applies the adaptive per-outlet threshold.

    Constructed with validated ``Settings``; each threshold/signal parameter
    is read from config so tuning is a config change, never a code change.
    """

    def __init__(self, settings: Settings) -> None:
        """Bind every tunable from validated Settings for this detector."""
        self._min_images = settings.min_images_per_outlet
        self._min_images_for_isolation_forest = settings.min_images_for_isolation_forest
        self._k_neighbors = settings.k_neighbors
        self._mad_k = settings.mad_k
        self._score_floor = settings.score_floor
        self._score_decimals = settings.score_decimals
        self._random_seed = settings.random_seed
        self._isolation_forest_estimators = settings.isolation_forest_estimators
        (
            self._centroid_weight,
            self._knn_weight,
            self._isolation_forest_weight,
        ) = settings.fusion_weights()
        self._logger = get_logger("ensemble_detector")

    def detect(
        self,
        embeddings: np.ndarray,
        file_names: Sequence[str],
    ) -> DetectionOutcome:
        """Flag outliers for one outlet and rank every image by suspicion.

        Outlets with fewer than ``max(2, min_images_per_outlet)`` images have
        no reference distribution (SPEC §5.1) and are returned with an empty
        flag list. Otherwise: cosine matrix -> centroid/kNN signals + Isolation
        Forest -> fusion -> adaptive threshold -> flags + reasons + ranking.
        """
        names = list(file_names)
        image_count = embeddings.shape[0]
        if image_count != len(names):
            raise ValueError(
                "embedding count and file-name count must match "
                f"(got {image_count} vs {len(names)})"
            )
        if image_count < max(2, self._min_images):
            return self._empty_outcome(names)

        similarity_matrix = cosine_similarity_matrix(embeddings)
        centroid = robust_centroid(embeddings)
        centroid_distance = centroid_distances(embeddings, centroid)
        knn_consensus = knn_signal(similarity_matrix, self._k_neighbors)

        if image_count >= self._min_images_for_isolation_forest:
            isolation_forest = isolation_forest_scores(
                embeddings,
                self._random_seed,
                self._isolation_forest_estimators,
            )
        else:
            isolation_forest = None

        fused = fused_suspicion_scores(
            centroid_distance,
            knn_consensus,
            isolation_forest,
            self._centroid_weight,
            self._knn_weight,
            self._isolation_forest_weight,
            image_count,
            self._min_images_for_isolation_forest,
        )

        threshold = adaptive_flag_threshold(fused, self._mad_k, self._score_floor)
        # Flag on the raw fused score (SPEC §11.1); rounding only shapes the
        # reported/ranked values, so a borderline image is never dropped by
        # output precision.
        flagged_mask = fused > threshold
        rounded_scores = np.round(fused, self._score_decimals)

        flagged = [
            FlaggedImage(
                file_name=names[index],
                suspicion_score=float(rounded_scores[index]),
                reason=reason_for_signals(
                    float(centroid_distance[index]),
                    float(knn_consensus[index]),
                    float(isolation_forest[index])
                    if isolation_forest is not None
                    else None,
                    self._centroid_weight,
                    self._knn_weight,
                    self._isolation_forest_weight,
                ),
            )
            for index in np.flatnonzero(flagged_mask)
        ]

        ranked = sorted(
            zip(names, rounded_scores, strict=True),
            key=lambda pair: (-float(pair[1]), pair[0]),
        )
        ranking = [name for name, _ in ranked]
        suspicion_scores = [float(score) for score in rounded_scores]

        self._logger.info(
            "outlet_detected",
            image_count=image_count,
            flagged_count=len(flagged),
            threshold=round(float(threshold), self._score_decimals),
        )
        return DetectionOutcome(
            file_names=names,
            suspicion_scores=suspicion_scores,
            flagged=flagged,
            ranking=ranking,
        )

    def _empty_outcome(self, names: list[str]) -> DetectionOutcome:
        """Return a no-flag outcome for outlets without a reference distribution."""
        self._logger.info(
            "outlet_below_reference_minimum",
            image_count=len(names),
            min_images_per_outlet=self._min_images,
        )
        return DetectionOutcome(
            file_names=names,
            suspicion_scores=[0.0] * len(names),
            flagged=[],
            ranking=sorted(names),
        )
