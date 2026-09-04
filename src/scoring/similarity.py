"""Pairwise cosine-similarity matrix (SPEC §10.2, ED-2).

Embeddings are L2-normalized, so cosine similarity is a plain dot product.
The diagonal (self-similarity) is explicitly excluded by overwriting it with
-1.0, the minimum possible cosine value, so nearest-neighbour statistics can
never select an image as its own neighbour.
"""

from __future__ import annotations

import numpy as np

from core.exceptions import DetectionError


def cosine_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """Return the N x N cosine-similarity matrix with the diagonal excluded.

    ``embeddings`` is an (N, d) array of L2-normalized rows; the result has
    zero diagonal by construction (overwritten with -1.0) and is symmetric.
    """
    if embeddings.ndim != 2:
        raise DetectionError(f"expected a 2D embedding matrix, got {embeddings.ndim}D")
    matrix = np.asarray(embeddings @ embeddings.T)
    np.fill_diagonal(matrix, -1.0)
    return matrix
