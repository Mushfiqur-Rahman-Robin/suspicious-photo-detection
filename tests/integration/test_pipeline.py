"""Integration tests: end-to-end pipeline on real synthetic images (P4.x, Gate 4).

Uses the PixelMeanEmbedder (a real image pipeline: bytes -> decode -> embed)
so the whole load->embed->score->detect->report flow is exercised on genuine
image files without any model download.
"""

from __future__ import annotations

import json


def _consistent_outlet_rgb() -> tuple[int, int, int]:
    return (200, 40, 40)


def _unrelated_rgb() -> tuple[int, int, int]:
    return (10, 10, 220)


def _build_dataset(dataset_factory):
    consistent = _consistent_outlet_rgb()
    unrelated = _unrelated_rgb()
    return dataset_factory(
        {
            "outlet_clean": {f"img_{index:03d}.jpg": consistent for index in range(12)},
            "outlet_fake": {
                **{f"img_{index:03d}.jpg": consistent for index in range(12)},
                "unrelated.jpg": unrelated,
            },
        }
    )


def test_full_run_flags_injected_unrelated_image(runner_factory, dataset_factory):
    dataset_root = _build_dataset(dataset_factory)
    runner = runner_factory(dataset_dir=dataset_root)
    runner.run_full()

    results = json.loads(
        (runner._settings.output_dir / "results.json").read_text(encoding="utf-8")
    )
    fake_outlet = next(
        entry for entry in results if entry["outlet_id"] == "outlet_fake"
    )
    assert "unrelated.jpg" in {
        flag["file_name"] for flag in fake_outlet["flagged_images"]
    }
    flag = next(
        flag
        for flag in fake_outlet["flagged_images"]
        if flag["file_name"] == "unrelated.jpg"
    )
    assert 0.5 < flag["suspicion_score"] <= 1.0
    assert flag["reason"]


def test_clean_outlet_has_empty_flags_and_is_present(runner_factory, dataset_factory):
    dataset_root = _build_dataset(dataset_factory)
    runner = runner_factory(dataset_dir=dataset_root)
    runner.run_full()

    payload = json.loads(
        (runner._settings.output_dir / "results.json").read_text(encoding="utf-8")
    )
    clean = next(entry for entry in payload if entry["outlet_id"] == "outlet_clean")
    assert clean["flagged_images"] == []
    assert clean["total_images"] == 12


def test_every_outlet_present_exactly_once(runner_factory, dataset_factory):
    dataset_root = _build_dataset(dataset_factory)
    runner = runner_factory(dataset_dir=dataset_root)
    runner.run_full()

    payload = json.loads(
        (runner._settings.output_dir / "results.json").read_text(encoding="utf-8")
    )
    outlet_ids = [entry["outlet_id"] for entry in payload]
    assert len(outlet_ids) == len(set(outlet_ids))
    assert set(outlet_ids) == {"outlet_clean", "outlet_fake"}


def test_ranking_covers_all_images_per_outlet(runner_factory, dataset_factory):
    dataset_root = _build_dataset(dataset_factory)
    runner = runner_factory(dataset_dir=dataset_root)
    runner.run_full()

    payload = json.loads(
        (runner._settings.output_dir / "results.json").read_text(encoding="utf-8")
    )
    for entry in payload:
        assert (
            sorted(entry["ranking"])
            == sorted(f"img_{index:03d}.jpg" for index in range(12))
            or entry["outlet_id"] == "outlet_fake"
        )
    fake = next(entry for entry in payload if entry["outlet_id"] == "outlet_fake")
    assert sorted(fake["ranking"]) == sorted(
        [f"img_{index:03d}.jpg" for index in range(12)] + ["unrelated.jpg"]
    )
    assert fake["ranking"][0] == "unrelated.jpg"  # most suspicious first


def test_all_scores_within_unit_interval(runner_factory, dataset_factory):
    dataset_root = _build_dataset(dataset_factory)
    runner = runner_factory(dataset_dir=dataset_root)
    runner.run_full()

    payload = json.loads(
        (runner._settings.output_dir / "results.json").read_text(encoding="utf-8")
    )
    for entry in payload:
        for flag in entry["flagged_images"]:
            assert 0.0 <= flag["suspicion_score"] <= 1.0


def test_run_writes_summary_and_write_up(runner_factory, dataset_factory):
    dataset_root = _build_dataset(dataset_factory)
    runner = runner_factory(dataset_dir=dataset_root)
    runner.run_full()

    output_dir = runner._settings.output_dir
    assert (output_dir / "results.json").is_file()
    assert (output_dir / "results.csv").is_file()
    assert (output_dir / "run_summary.json").is_file()
    assert (output_dir / "write_up.md").is_file()


def test_embed_only_populates_cache_without_results(runner_factory, dataset_factory):
    dataset_root = _build_dataset(dataset_factory)
    runner = runner_factory(dataset_dir=dataset_root)
    runner.run_embed()

    assert not (runner._settings.output_dir / "results.json").exists()
    cache_files = list(runner._settings.cache_dir.rglob("*.npy"))
    # 2 distinct image contents (consistent red, unrelated blue); identical
    # bytes share one content-addressed entry (ED-6)
    assert len(cache_files) == 2


def test_detect_from_cache_reproduces_results(runner_factory, dataset_factory):
    dataset_root = _build_dataset(dataset_factory)
    runner = runner_factory(dataset_dir=dataset_root)
    runner.run_full()
    reference = (runner._settings.output_dir / "results.json").read_bytes()

    detector = runner_factory(dataset_dir=dataset_root)
    detector.run_detect()
    assert (detector._settings.output_dir / "results.json").read_bytes() == reference


def test_detect_without_cache_errors(runner_factory, dataset_factory):
    import pytest

    from core.exceptions import CacheError

    dataset_root = _build_dataset(dataset_factory)
    runner = runner_factory(dataset_dir=dataset_root)
    with pytest.raises(CacheError):
        runner.run_detect()


def test_report_regenerates_outputs_from_cache(runner_factory, dataset_factory):
    dataset_root = _build_dataset(dataset_factory)
    runner = runner_factory(dataset_dir=dataset_root)
    runner.run_full()
    runner._settings.output_dir.joinpath("results.csv").unlink()
    runner._settings.output_dir.joinpath("write_up.md").unlink()

    reporter = runner_factory(dataset_dir=dataset_root)
    reporter.run_report()
    assert (reporter._settings.output_dir / "results.csv").is_file()
    assert (reporter._settings.output_dir / "write_up.md").is_file()


def test_report_without_cached_results_errors(runner_factory, dataset_factory):
    import pytest

    from core.exceptions import WriteError

    dataset_root = _build_dataset(dataset_factory)
    runner = runner_factory(dataset_dir=dataset_root)
    with pytest.raises(WriteError):
        runner.run_report()


def test_empty_outlet_folder_is_reported(runner_factory, dataset_factory):

    dataset_root = _build_dataset(dataset_factory)
    (dataset_root / "outlet_empty").mkdir()
    runner = runner_factory(dataset_dir=dataset_root)
    runner.run_full()

    payload = json.loads(
        (runner._settings.output_dir / "results.json").read_text(encoding="utf-8")
    )
    empty = next(entry for entry in payload if entry["outlet_id"] == "outlet_empty")
    assert empty["total_images"] == 0
    assert empty["flagged_images"] == []
