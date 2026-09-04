"""In-memory pipeline entities (SPEC §6.2).

These are the typed currency that flows between stages. They are plain
dataclasses on purpose: `core` stays free of torch/numpy/sklearn imports
(ARCHITECTURE §4), so numpy vectors are referenced only under
``TYPE_CHECKING`` while the real arrays are passed around unmodified.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from .output_schema import FlaggedImage

if TYPE_CHECKING:
    import numpy as np


@dataclass(slots=True)
class ImageRecord:
    """One image discovered in an outlet folder.

    ``file_name`` and ``path`` identify the file; ``content_hash`` is the
    sha256 of the decoded image bytes and keys the embedding cache (ED-6).
    ``embedding`` is attached lazily after extraction so the record can be
    inspected in one place while staying I/O-free.
    """

    file_name: str
    path: Path
    content_hash: str
    embedding: Embedding | None = None


@dataclass(frozen=True, slots=True)
class Embedding:
    """An L2-normalized embedding vector plus the provenance for cache keys.

    ``model`` + ``model_version`` repeat the cache-key namespace so a vector
    is never confused with one from a different model or weight snapshot.
    """

    vector: np.ndarray
    model: str
    model_version: str
    content_hash: str
    dim: int


def _default_image_records() -> list[ImageRecord]:
    """Empty image-list factory so the default is explicitly typed."""
    return []


@dataclass(slots=True)
class Outlet:
    """A discovered outlet: its folder-name id and its image records."""

    outlet_id: str
    images: list[ImageRecord] = field(default_factory=_default_image_records)


@dataclass(frozen=True, slots=True)
class SuspicionProfile:
    """Per-image suspicion signals (SPEC §6.2).

    Kept separate from the output schema so raw signals never leak into the
    hard JSON/CSV contract; only the fused, rounded score is emitted.
    """

    file_name: str
    centroid_distance: float
    knn_consensus: float
    isolation_forest: float | None
    fused_score: float


@dataclass(frozen=True, slots=True)
class SuspicionSignals:
    """Array-form signals for one outlet (N images) shared by scoring/detection."""

    centroid_distance: np.ndarray
    knn_consensus: np.ndarray
    isolation_forest: np.ndarray | None
    fused_scores: np.ndarray


@dataclass(frozen=True, slots=True)
class DetectionOutcome:
    """Result of the detection stage for one outlet.

    ``suspicion_scores`` are the per-image fused scores (rounded to
    ``score_decimals``), aligned with ``file_names``; ``flagged`` holds the
    schema-valid ``FlaggedImage`` entries; ``ranking`` is every image ordered
    most -> least suspicious (SPEC §6.1, FR7).
    """

    file_names: list[str]
    suspicion_scores: list[float]
    flagged: list[FlaggedImage]
    ranking: list[str]


@dataclass(frozen=True, slots=True)
class WriteSummary:
    """Files produced by the ResultWriter (SPEC §6.1, FR6)."""

    json_path: Path
    csv_path: Path
    outlet_count: int
