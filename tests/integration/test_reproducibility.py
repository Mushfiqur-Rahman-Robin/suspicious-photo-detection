"""Integration tests: reproducibility (SPEC §13, ED-6, P5.2).

Two identical runs must produce byte-identical results, and a cold vs warm
cache must produce identical results.
"""

from __future__ import annotations

import json


def _dataset(dataset_factory):
    return dataset_factory(
        {
            "outlet_a": {f"img_{i:03d}.jpg": (200, 40, 40) for i in range(8)},
            "outlet_b": {
                **{f"img_{i:03d}.jpg": (120, 120, 10) for i in range(6)},
                "odd.jpg": (10, 10, 220),
            },
        }
    )


def _read_json(output_dir, name):
    return (output_dir / name).read_bytes()


def test_two_full_runs_are_byte_identical(runner_factory, dataset_factory, tmp_path):
    dataset_root = _dataset(dataset_factory)
    first = runner_factory(dataset_dir=dataset_root, output_dir=tmp_path / "out1")
    first.run_full()
    second = runner_factory(dataset_dir=dataset_root, output_dir=tmp_path / "out2")
    second.run_full()

    assert _read_json(tmp_path / "out1", "results.json") == _read_json(
        tmp_path / "out2", "results.json"
    )
    assert _read_json(tmp_path / "out1", "results.csv") == _read_json(
        tmp_path / "out2", "results.csv"
    )


def test_cold_vs_warm_cache_identical(runner_factory, dataset_factory, tmp_path):
    dataset_root = _dataset(dataset_factory)
    cold = runner_factory(dataset_dir=dataset_root, output_dir=tmp_path / "cold")
    cold.run_full()
    warm = runner_factory(
        dataset_dir=dataset_root,
        output_dir=tmp_path / "warm",
        cache_dir=tmp_path / "cache",
    )
    warm.run_full()

    assert _read_json(tmp_path / "cold", "results.json") == _read_json(
        tmp_path / "warm", "results.json"
    )


def test_cached_results_do_not_embed_timestamps(runner_factory, dataset_factory):
    dataset_root = _dataset(dataset_factory)
    runner = runner_factory(dataset_dir=dataset_root)
    runner.run_full()
    results_text = (runner._settings.output_dir / "results.json").read_text(
        encoding="utf-8"
    )
    assert "started_at" not in results_text
    assert "run_id" not in results_text


def test_summary_records_kpis(runner_factory, dataset_factory):
    dataset_root = _dataset(dataset_factory)
    runner = runner_factory(dataset_dir=dataset_root)
    runner.run_full()
    summary = json.loads(
        (runner._settings.output_dir / "run_summary.json").read_text(encoding="utf-8")
    )
    assert summary["total_outlets"] == 2
    assert summary["total_images"] == 15
    assert summary["total_flagged_images"] == 1
    assert summary["outlets_with_flags"] == 1
    assert summary["stage_timings"]
    assert summary["cache_hits"] == 0
    assert summary["cache_misses"] == 15
