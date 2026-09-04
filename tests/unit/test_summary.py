"""Unit tests: run summary (SPEC §14, P4.5)."""

from __future__ import annotations

import json

from config.settings import Settings
from core.output_schema import FlaggedImage, OutletResult, build_outlet_result
from reporting.summary import build_run_summary, write_run_summary


def _results() -> list[OutletResult]:
    return [
        build_outlet_result(
            "outlet_a",
            4,
            [FlaggedImage(file_name="a2.jpg", suspicion_score=0.8, reason="r")],
            ["a2.jpg", "a1.jpg", "a3.jpg", "a4.jpg"],
        ),
        build_outlet_result("outlet_b", 2, [], ["b1.jpg", "b2.jpg"]),
    ]


def test_summary_aggregates_counts_and_kpis():
    settings = Settings()
    summary = build_run_summary(
        run_id="run-1",
        settings=settings,
        results=_results(),
        timings={"load": 1.0, "embed": 4.0, "detect": 0.5, "report": 0.1},
        cache_hits=2,
        cache_misses=4,
    )
    assert summary.total_outlets == 2
    assert summary.total_images == 6
    assert summary.outlets_with_flags == 1
    assert summary.total_flagged_images == 1
    assert summary.embeddings_per_second == 6 / 4.0
    assert summary.cache_hits == 2
    assert summary.cache_misses == 4
    assert summary.total_wall_seconds == 5.6


def test_summary_embed_seconds_zero_is_guarded():
    summary = build_run_summary(
        run_id="r",
        settings=Settings(),
        results=_results(),
        timings={},
        cache_hits=0,
        cache_misses=0,
    )
    assert summary.embeddings_per_second == 0.0


def test_summary_version_uses_dino_hub_ref():
    settings = Settings()
    summary = build_run_summary("r", settings, _results(), {}, 0, 0)
    assert summary.model_version == settings.dino_v2_hub_ref


def test_write_run_summary_persists_json(output_dir):
    summary = build_run_summary("r", Settings(), _results(), {"load": 0.5}, 1, 1)
    path = write_run_summary(summary, output_dir)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "r"
    assert payload["total_outlets"] == 2
    assert "stage_timings" in payload
