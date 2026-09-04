"""L2 normalization helper (ED-2).

All signals are defined on L2-normalized embeddings so cosine similarity is a
dot product (SPEC §10.2). Kept as a pure function so it is unit-testable
without a model and shared by every embedder adapter.
"""

from __future__ import annotations

import numpy as np


def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    """Normalize each row of ``vectors`` to unit length (safe for zero rows).

    Zero rows (numerically degenerate embeddings) are left as zeros so the
    caller's distance math stays well-defined; they are never NaN.
    """
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return np.asarray(
        np.divide(
            vectors,
            norms,
            out=np.zeros_like(vectors, dtype=vectors.dtype),
            where=norms > 0.0,
        )
    )
