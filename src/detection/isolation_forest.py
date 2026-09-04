"""Seeded, deterministic Isolation Forest anomaly signal (SPEC §10.3, ED-4).

The multivariate isolation structure of the outlet's embeddings is captured
by scikit-learn's IsolationForest. Scores are min-max normalized over the
outlet to [0, 1] (SPEC §10.3) and the forest is seeded from the global
``RANDOM_SEED`` so a re-run yields identical values (ED-6).
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest  # type: ignore[import-untyped]

from core.exceptions import DetectionError

DETERMINISTIC_TOLERANCE = 1e-9


def isolation_forest_scores(
    embeddings: np.ndarray,
    random_seed: int,
    n_estimators: int,
) -> np.ndarray:
    """Return per-image Isolation Forest anomaly scores normalized to [0, 1].

    ``decision_function`` returns lower values for more anomalous points, so
    the signal is its negation; min-max scaling over the outlet maps it to
    [0, 1]. A degenerate (constant) score vector maps to the neutral 0.5.
    """
    if embeddings.shape[0] < 2:
        raise DetectionError("Isolation Forest needs at least 2 images")
    forest: Any = IsolationForest(
        n_estimators=n_estimators,
        random_state=random_seed,
        n_jobs=1,
    )
    forest.fit(embeddings)
    raw = -forest.decision_function(embeddings)
    minimum = float(np.min(raw))
    maximum = float(np.max(raw))
    if maximum - minimum < DETERMINISTIC_TOLERANCE:
        return np.full(raw.shape, 0.5, dtype=np.float64)
    return np.asarray((raw - minimum) / (maximum - minimum))
