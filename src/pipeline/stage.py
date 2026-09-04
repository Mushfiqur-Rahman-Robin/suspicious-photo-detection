"""Pipeline stage abstraction (Template Method, SPEC §19, P4.1).

Each stage wraps its work in a uniform lifecycle: the base class times the
execution, records the duration in the shared context, and logs completion.
Concrete stages implement ``execute`` only, giving every stage identical
timing/logging behavior.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter

import numpy as np
from structlog.stdlib import BoundLogger

from config.settings import Settings
from core.entities import Embedding, Outlet
from core.output_schema import OutletResult, build_outlet_result
from core.ports import OutlierDetector
from embedding.service import EmbeddingService
from io_layer.dataset_loader import DatasetLoader
from io_layer.result_writer import ResultWriter


def _default_outlets() -> list[Outlet]:
    """Empty outlet-list factory (explicitly typed default)."""
    return []


def _default_embeddings_map() -> dict[str, list[Embedding]]:
    """Empty embedding-map factory (explicitly typed default)."""
    return {}


def _default_results() -> list[OutletResult]:
    """Empty results-list factory (explicitly typed default)."""
    return []


def _default_timings() -> dict[str, float]:
    """Empty timing-map factory (explicitly typed default)."""
    return {}


@dataclass
class StageContext:
    """Mutable, shared state flowing through the pipeline stages.

    The runner populates the ports/services once and each stage reads or
    fills the data fields; stages never mutate another stage's inputs.
    """

    settings: Settings
    logger: BoundLogger
    loader: DatasetLoader
    embedding_service: EmbeddingService
    detector: OutlierDetector
    writer: ResultWriter
    dataset_dir: Path
    output_dir: Path
    cache_only: bool = False
    outlets: list[Outlet] = field(default_factory=_default_outlets)
    embeddings_by_outlet: dict[str, list[Embedding]] = field(
        default_factory=_default_embeddings_map
    )
    results: list[OutletResult] = field(default_factory=_default_results)
    timings: dict[str, float] = field(default_factory=_default_timings)


class PipelineStage(ABC):
    """Base class giving every stage a timed, logged execution lifecycle."""

    def __init__(self, context: StageContext, stage_name: str) -> None:
        """Bind the shared context and this stage's name for timing/logging."""
        self._context = context
        self._stage_name = stage_name

    def run(self) -> None:
        """Execute the stage and record its wall-clock duration."""
        start = perf_counter()
        self.execute()
        duration = perf_counter() - start
        self._context.timings[self._stage_name] = duration
        self._context.logger.info(
            "stage_completed",
            stage=self._stage_name,
            duration_seconds=round(duration, 4),
        )

    @abstractmethod
    def execute(self) -> None:
        """Perform the stage's work against ``self._context``."""


class LoadStage(PipelineStage):
    """Discover outlets and image records under the dataset root (FR1)."""

    def __init__(self, context: StageContext) -> None:
        """Bind the context under the ``load`` stage name."""
        super().__init__(context, "load")

    def execute(self) -> None:
        """Discover all outlets into the shared context (FR1)."""
        self._context.outlets = self._context.loader.discover_outlets(
            self._context.dataset_dir
        )
        self._context.logger.info(
            "outlets_discovered",
            outlet_count=len(self._context.outlets),
            dataset_dir=str(self._context.dataset_dir),
        )


class EmbedStage(PipelineStage):
    """Extract (and cache) embeddings for every outlet's images (FR2)."""

    def __init__(self, context: StageContext) -> None:
        """Bind the context under the ``embed`` stage name."""
        super().__init__(context, "embed")

    def execute(self) -> None:
        """Extract cached embeddings for every outlet into the context (FR2)."""
        embeddings_by_outlet: dict[str, list[Embedding]] = {}
        for outlet in self._context.outlets:
            embeddings_by_outlet[outlet.outlet_id] = (
                self._context.embedding_service.embed_records(
                    outlet.images,
                    cache_only=self._context.cache_only,
                )
            )
        self._context.embeddings_by_outlet = embeddings_by_outlet
        service = self._context.embedding_service
        self._context.logger.info(
            "embeddings_extracted",
            cache_hits=service.hit_count,
            cache_misses=service.miss_count,
        )


class DetectStage(PipelineStage):
    """Score, detect, and assemble schema-valid results per outlet (FR3-FR5)."""

    def __init__(self, context: StageContext) -> None:
        """Bind the context under the ``detect`` stage name."""
        super().__init__(context, "detect")

    def execute(self) -> None:
        """Score/detect every outlet and assemble schema-valid results (FR3-FR5)."""
        results: list[OutletResult] = []
        for outlet in self._context.outlets:
            embeddings = self._context.embeddings_by_outlet[outlet.outlet_id]
            matrix = self._stack_embeddings(embeddings)
            outcome = self._context.detector.detect(
                matrix,
                [record.file_name for record in outlet.images],
            )
            results.append(
                build_outlet_result(
                    outlet_id=outlet.outlet_id,
                    total_images=len(outlet.images),
                    flagged_images=list(outcome.flagged),
                    ranking=list(outcome.ranking),
                )
            )
        self._context.results = results

    def _stack_embeddings(self, embeddings: list[Embedding]) -> np.ndarray:
        """Stack per-image vectors into one (N, d) matrix, empty-safe."""
        if not embeddings:
            return np.zeros((0, self._context.settings.embedding_dim))
        return np.stack([embedding.vector for embedding in embeddings])


class ReportStage(PipelineStage):
    """Write the schema-valid JSON + CSV results (FR6)."""

    def __init__(self, context: StageContext) -> None:
        """Bind the context under the ``report`` stage name."""
        super().__init__(context, "report")

    def execute(self) -> None:
        """Write the JSON + CSV results into the output directory (FR6)."""
        self._context.writer.write_results(
            self._context.results,
            self._context.output_dir,
        )
