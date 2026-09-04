"""Run-summary computation and persistence (SPEC §14).

Aggregates the KPIs a reviewer needs to trust the run: image counts, cache
hits/misses, embedding throughput, flag counts, and per-stage wall-clock.
The summary is diagnostic (it carries a run id + timestamp) and never leaks
into the byte-identical ``results.json``/``results.csv`` contract.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from config.settings import Settings
from core.exceptions import WriteError
from core.output_schema import OutletResult
from embedding.device import resolve_torch_device
from observability.logging import get_logger

RUN_SUMMARY_FILENAME = "run_summary.json"


def _default_timings() -> dict[str, float]:
    """Empty timing-map factory (explicitly typed default)."""
    return {}


@dataclass(frozen=True, slots=True)
class RunSummary:
    """Aggregated diagnostics for one pipeline run."""

    run_id: str
    started_at: str
    model: str
    model_version: str
    embedding_dim: int
    device: str
    random_seed: int
    dataset_dir: str
    output_dir: str
    total_outlets: int
    total_images: int
    cache_hits: int
    cache_misses: int
    embeddings_per_second: float
    outlets_with_flags: int
    total_flagged_images: int
    stage_timings: dict[str, float] = field(default_factory=_default_timings)
    total_wall_seconds: float = 0.0


def build_run_summary(
    run_id: str,
    settings: Settings,
    results: list[OutletResult],
    timings: dict[str, float],
    cache_hits: int,
    cache_misses: int,
) -> RunSummary:
    """Derive a RunSummary from the settings, results, and stage timings."""
    embed_duration = timings.get("embed", 0.0)
    total_images = sum(result.total_images for result in results)
    embeddings_per_second = total_images / embed_duration if embed_duration > 0 else 0.0
    return RunSummary(
        run_id=run_id,
        started_at=datetime.now(UTC).isoformat(),
        model=settings.embedding_model.value,
        model_version=_embedder_version(settings),
        embedding_dim=settings.embedding_dim,
        device=str(resolve_torch_device(settings.device)),
        random_seed=settings.random_seed,
        dataset_dir=str(settings.dataset_dir),
        output_dir=str(settings.output_dir),
        total_outlets=len(results),
        total_images=total_images,
        cache_hits=cache_hits,
        cache_misses=cache_misses,
        embeddings_per_second=embeddings_per_second,
        outlets_with_flags=sum(1 for result in results if result.flagged_images),
        total_flagged_images=sum(len(result.flagged_images) for result in results),
        stage_timings={name: round(duration, 4) for name, duration in timings.items()},
        total_wall_seconds=round(sum(timings.values()), 4),
    )


def write_run_summary(summary: RunSummary, output_dir: Path) -> Path:
    """Write ``run_summary.json`` under ``output_dir`` and return its path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / RUN_SUMMARY_FILENAME
    try:
        path.write_text(json_dumps(summary), encoding="utf-8")
    except OSError as exc:
        raise WriteError(f"unable to write run summary to {path}: {exc}") from exc
    get_logger("run_summary").info(
        "run_summary_written",
        path=str(path),
        total_outlets=summary.total_outlets,
        total_flagged_images=summary.total_flagged_images,
    )
    return path


def _embedder_version(settings: Settings) -> str:
    """Expose a human-readable embedder/version string for the summary."""
    if settings.embedding_model.value == "clip":
        return "open_clip (pinned via clip extra lockfile)"
    return settings.dino_v2_hub_ref


def json_dumps(summary: RunSummary) -> str:
    """Serialize the summary deterministically (indented, sorted keys)."""
    import json

    return json.dumps(asdict(summary), indent=2, sort_keys=True)
