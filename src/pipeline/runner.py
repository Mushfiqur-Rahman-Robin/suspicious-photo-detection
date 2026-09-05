"""Pipeline runner - the composition root and facade (SPEC §19, ARCH §6).

The runner wires the ports (loader, embedder + cache, detector, writer),
orchestrates the stages in the canonical order (load -> embed -> detect ->
report), tracks per-stage timing and KPIs, and emits the run summary and the
one-page write-up. It contains no ML or I/O internals.
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from config.settings import Settings
from core.exceptions import WriteError
from core.output_schema import OutletResult
from core.ports import Embedder
from detection.factory import create_detector
from embedding.factory import create_embedder
from embedding.service import EmbeddingService
from io_layer.dataset_loader import DatasetLoader
from io_layer.embedding_cache import EmbeddingCache
from io_layer.image_utils import decode_image_from_path
from io_layer.result_writer import ResultWriter
from observability.logging import (
    bind_run_context,
    clear_run_context,
    configure_logging,
    get_logger,
)
from pipeline.stage import (
    DetectStage,
    EmbedStage,
    LoadStage,
    ReportStage,
    StageContext,
)
from reporting.summary import build_run_summary, write_run_summary
from reporting.write_up import compose_write_up, write_write_up


class PipelineRunner:
    """Facade over the staged pipeline; the single entry point for all CLI commands.

    ``embedder`` may be injected for testing (a fake implementing the Embedder
    port), which keeps end-to-end tests fast and deterministic without a real
    model download.
    """

    def __init__(self, settings: Settings, embedder: Embedder | None = None) -> None:
        """Wire all ports (loader/embedder+cache/detector/writer) and bind the run context."""
        configure_logging(
            settings.log_level,
            settings.log_dir,
            settings.log_filename,
        )
        self._settings = settings
        self._logger = get_logger("pipeline_runner")
        self._run_id = uuid4().hex
        bind_run_context(run_id=self._run_id)

        cache = EmbeddingCache(settings.cache_dir)
        resolved_embedder = (
            embedder if embedder is not None else create_embedder(settings)
        )
        self._embedding_service = EmbeddingService(
            embedder=resolved_embedder,
            cache=cache,
            decode_image=lambda record: decode_image_from_path(
                record.path,
                settings.max_image_dimension,
                settings.max_image_pixels,
            ),
        )
        loader = DatasetLoader(
            min_images_per_outlet=settings.min_images_per_outlet,
            ignore_corrupt_images=settings.ignore_corrupt_images,
            max_image_dimension=settings.max_image_dimension,
            max_image_pixels=settings.max_image_pixels,
        )
        self._loader = loader
        self._detector = create_detector(settings)
        self._writer = ResultWriter(settings)

    def run_full(self) -> None:
        """Run load -> embed -> detect -> report and summarize (``spd run``)."""
        context = self._new_context(cache_only=False)
        LoadStage(context).run()
        EmbedStage(context).run()
        DetectStage(context).run()
        ReportStage(context).run()
        self._finalize(context)

    def run_embed(self) -> None:
        """Only discover + embed, populating the cache (``spd embed``)."""
        context = self._new_context(cache_only=False)
        LoadStage(context).run()
        EmbedStage(context).run()
        self._logger.info(
            "embed_only_complete",
            cache_hits=self._embedding_service.hit_count,
            cache_misses=self._embedding_service.miss_count,
        )

    def run_detect(self) -> None:
        """Score + detect from cached embeddings and write results (``spd detect``)."""
        context = self._new_context(cache_only=True)
        LoadStage(context).run()
        EmbedStage(context).run()
        DetectStage(context).run()
        ReportStage(context).run()
        self._finalize(context)

    def run_report(self) -> None:
        """Regenerate JSON + CSV + write-up from cached results (``spd report``)."""
        results_json = self._settings.output_dir / self._settings.results_json_filename
        if not results_json.is_file():
            raise WriteError(
                f"no cached results found at {results_json}; run `spd run` or `spd detect` first"
            )
        results = self._load_cached_results(results_json)
        self._writer.write_results(results, self._settings.output_dir)
        summary = build_run_summary(
            run_id=self._run_id,
            settings=self._settings,
            results=results,
            timings={},
            cache_hits=0,
            cache_misses=0,
        )
        write_up = compose_write_up(
            summary,
            max_chars=self._settings.write_up_max_chars,
        )
        write_write_up(write_up, self._settings.output_dir, self._settings)
        self._logger.info(
            "report_regenerated",
            outlet_count=len(results),
            output_dir=str(self._settings.output_dir),
        )

    def _new_context(self, cache_only: bool) -> StageContext:
        """Build a fresh StageContext wired with the runner's components."""
        return StageContext(
            settings=self._settings,
            logger=self._logger,
            loader=self._loader,
            embedding_service=self._embedding_service,
            detector=self._detector,
            writer=self._writer,
            dataset_dir=self._settings.dataset_dir,
            output_dir=self._settings.output_dir,
            cache_only=cache_only,
        )

    def _finalize(self, context: StageContext) -> None:
        """Write the run summary + write-up and log the end-of-run KPIs."""
        summary = build_run_summary(
            run_id=self._run_id,
            settings=self._settings,
            results=context.results,
            timings=context.timings,
            cache_hits=self._embedding_service.hit_count,
            cache_misses=self._embedding_service.miss_count,
            embedding_latency_seconds=self._embedding_service.embedding_latency_seconds,
        )
        write_run_summary(summary, context.output_dir, self._settings)
        write_up = compose_write_up(
            summary,
            max_chars=self._settings.write_up_max_chars,
        )
        write_write_up(write_up, context.output_dir, self._settings)
        clear_run_context()
        self._logger.info(
            "pipeline_complete",
            run_id=self._run_id,
            total_outlets=summary.total_outlets,
            total_images=summary.total_images,
            flagged_outlets=summary.outlets_with_flags,
            total_flagged_images=summary.total_flagged_images,
            cache_hits=summary.cache_hits,
            cache_misses=summary.cache_misses,
            embeddings_per_second=round(summary.embeddings_per_second, 1),
        )

    def _load_cached_results(self, results_json: Path) -> list[OutletResult]:
        """Validate the cached results.json back into OutletResult objects."""
        try:
            payload = json.loads(results_json.read_text(encoding="utf-8"))
            return [OutletResult.model_validate(entry) for entry in payload]
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise WriteError(
                f"cached results are invalid: {results_json}: {exc}"
            ) from exc
