"""Unit tests: result writer JSON + CSV (SPEC §6.1, FR6, P4.3)."""

from __future__ import annotations

import csv
import json

from config.settings import Settings
from core.output_schema import FlaggedImage, OutletResult, build_outlet_result
from io_layer.result_writer import ResultWriter


def _flagged_outlet() -> OutletResult:
    return build_outlet_result(
        outlet_id="outlet_0001",
        total_images=2,
        flagged_images=[
            FlaggedImage(
                file_name="img_02.jpg",
                suspicion_score=0.87,
                reason="Low similarity to cluster centroid",
            )
        ],
        ranking=["img_02.jpg", "img_01.jpg"],
    )


def _clean_outlet() -> OutletResult:
    return build_outlet_result(
        outlet_id="outlet_0002",
        total_images=3,
        flagged_images=[],
        ranking=["img_01.jpg", "img_02.jpg", "img_03.jpg"],
    )


def test_json_contains_every_outlet_exactly_once(output_dir):
    writer = ResultWriter(Settings())
    writer.write_results([_flagged_outlet(), _clean_outlet()], output_dir)
    payload = json.loads((output_dir / "results.json").read_text(encoding="utf-8"))
    assert [entry["outlet_id"] for entry in payload] == ["outlet_0001", "outlet_0002"]
    assert payload[1]["flagged_images"] == []
    assert payload[1]["total_images"] == 3
    assert payload[0]["flagged_images"][0]["suspicion_score"] == 0.87
    assert payload[0]["flagged_images"][0]["reason"]


def test_json_is_reproducible_across_writes(output_dir):
    writer = ResultWriter(Settings())
    writer.write_results([_flagged_outlet(), _clean_outlet()], output_dir)
    first = (output_dir / "results.json").read_bytes()
    writer.write_results([_flagged_outlet(), _clean_outlet()], output_dir)
    second = (output_dir / "results.json").read_bytes()
    assert first == second


def test_csv_has_header_and_rows(output_dir):
    writer = ResultWriter(Settings())
    writer.write_results([_flagged_outlet(), _clean_outlet()], output_dir)
    rows = list(csv.reader((output_dir / "results.csv").read_text().splitlines()))
    assert rows[0] == [
        "outlet_id",
        "total_images",
        "file_name",
        "suspicion_score",
        "reason",
    ]
    flagged_row = next(row for row in rows[1:] if row[0] == "outlet_0001")
    assert flagged_row[2] == "img_02.jpg"
    assert flagged_row[3] == "0.87"
    clean_row = next(row for row in rows[1:] if row[0] == "outlet_0002")
    assert clean_row[2:] == ["", "", ""]  # clean outlet represented with empty flags


def test_write_summary_reports_paths_and_count(output_dir):
    summary = ResultWriter(Settings()).write_results([_flagged_outlet()], output_dir)
    assert summary.json_path.name == "results.json"
    assert summary.csv_path.name == "results.csv"
    assert summary.outlet_count == 1


def test_filenames_are_centralized_in_settings(output_dir):
    settings = Settings(
        results_json_filename="custom_results.json",
        results_csv_filename="custom_results.csv",
    )
    summary = ResultWriter(settings).write_results([_flagged_outlet()], output_dir)
    assert summary.json_path.name == "custom_results.json"
    assert summary.csv_path.name == "custom_results.csv"
    assert (output_dir / "custom_results.json").is_file()
    assert (output_dir / "custom_results.csv").is_file()
    assert not (output_dir / "results.json").exists()
    assert not (output_dir / "results.csv").exists()
