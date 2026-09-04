"""Ports (protocols) that decouple stages (SPEC §19, ED-1/ED-9).

`core` declares these interfaces only and never imports the concrete
implementations, so the embedding model and the detection rule are swappable
via config without touching feature code. Numpy vectors and PIL images appear
only under ``TYPE_CHECKING`` to keep `core` free of heavy imports.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from .entities import DetectionOutcome, WriteSummary
from .output_schema import OutletResult

if TYPE_CHECKING:
    import numpy as np
    from PIL import Image


@runtime_checkable
class Embedder(Protocol):
    """Model-agnostic image-embedding port (ED-1).

    Implementations translate one model backend (DINOv2, CLIP) into the
    pipeline's currency: L2-normalized embedding rows.
    """

    @property
    def model_name(self) -> str:
        """Canonical model name used in cache keys and logs."""
        ...

    @property
    def model_version(self) -> str:
        """Pinned model/weight version used in cache keys (ED-6)."""
        ...

    @property
    def dim(self) -> int:
        """Embedding dimension produced by this model."""
        ...

    def embed_images(self, images: Sequence[Image.Image]) -> np.ndarray:
        """Encode PIL images into an (N, dim) L2-normalized float array."""
        ...


@runtime_checkable
class SimilarityScorer(Protocol):
    """Computes the pairwise cosine-similarity matrix (SPEC §10.2, ED-2)."""

    def compute_similarity_matrix(self, embeddings: np.ndarray) -> np.ndarray:
        """Return the N x N cosine matrix with the diagonal excluded."""
        ...


@runtime_checkable
class OutlierDetector(Protocol):
    """Fuses signals, thresholds, and produces flagged images (ED-4/ED-5/ED-9)."""

    def detect(
        self,
        embeddings: np.ndarray,
        file_names: Sequence[str],
    ) -> DetectionOutcome:
        """Flag outliers for one outlet given its L2-normalized embeddings."""
        ...


@runtime_checkable
class ResultWriter(Protocol):
    """Writes schema-valid JSON + CSV results (SPEC §6.1, FR6)."""

    def write_results(
        self,
        results: Sequence[OutletResult],
        output_dir: Path,
    ) -> WriteSummary:
        """Persist every outlet result to ``output_dir`` as JSON and CSV."""
        ...
