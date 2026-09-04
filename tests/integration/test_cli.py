"""Integration tests: `spd` CLI contract (SPEC §7, FR10, P4.4).

The real embedding factory is monkeypatched so no model is downloaded; the
fake embedder keeps the full command path (settings -> runner -> stages)
exercised end to end.
"""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from cli.app import app
from pipeline import runner as runner_module

cli_runner = CliRunner()


@pytest.fixture
def fake_embedder_override(monkeypatch, tmp_path):
    from conftest import PixelMeanEmbedder

    def _fake_factory(settings, model_name=None):
        return PixelMeanEmbedder()

    monkeypatch.setattr(runner_module, "create_embedder", _fake_factory)
    # Isolate the embedding cache and log dir per test so CLI runs never
    # share state or pollute the repo's logs/ directory.
    monkeypatch.setenv("CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))


def _make_cli_dataset(dataset_factory):
    return dataset_factory(
        {
            "outlet_clean": {f"img_{i:03d}.jpg": (200, 40, 40) for i in range(10)},
            "outlet_fake": {
                **{f"img_{i:03d}.jpg": (200, 40, 40) for i in range(10)},
                "unrelated.jpg": (10, 10, 220),
            },
        }
    )


def test_help_exits_zero():
    result = cli_runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "run" in result.stdout
    assert "embed" in result.stdout
    assert "detect" in result.stdout
    assert "report" in result.stdout


def test_run_produces_valid_output(fake_embedder_override, dataset_factory, tmp_path):
    dataset_root = _make_cli_dataset(dataset_factory)
    result = cli_runner.invoke(
        app,
        ["run", "--dataset", str(dataset_root), "--output", str(tmp_path / "results")],
    )
    assert result.exit_code == 0, result.stdout + result.stderr
    results_path = tmp_path / "results" / "results.json"
    payload = json.loads(results_path.read_text(encoding="utf-8"))
    assert {entry["outlet_id"] for entry in payload} == {"outlet_clean", "outlet_fake"}
    assert (tmp_path / "results" / "results.csv").is_file()


def test_embed_then_detect_then_report(
    fake_embedder_override, dataset_factory, tmp_path
):
    dataset_root = _make_cli_dataset(dataset_factory)
    embed_result = cli_runner.invoke(app, ["embed", "--dataset", str(dataset_root)])
    assert embed_result.exit_code == 0, embed_result.stderr

    detect_result = cli_runner.invoke(
        app,
        [
            "detect",
            "--dataset",
            str(dataset_root),
            "--output",
            str(tmp_path / "results"),
        ],
    )
    assert detect_result.exit_code == 0, detect_result.stderr
    assert (tmp_path / "results" / "results.json").is_file()

    report_result = cli_runner.invoke(
        app, ["report", "--output", str(tmp_path / "results")]
    )
    assert report_result.exit_code == 0, report_result.stderr
    assert (tmp_path / "results" / "write_up.md").is_file()


def test_detect_without_embeddings_exits_one(
    fake_embedder_override, dataset_factory, tmp_path
):
    dataset_root = _make_cli_dataset(dataset_factory)
    result = cli_runner.invoke(
        app,
        [
            "detect",
            "--dataset",
            str(dataset_root),
            "--output",
            str(tmp_path / "results"),
        ],
    )
    assert result.exit_code == 1
    assert "run `spd embed` first" in result.stderr


def test_invalid_model_flag_exits_two(fake_embedder_override, dataset_factory):
    dataset_root = _make_cli_dataset(dataset_factory)
    result = cli_runner.invoke(
        app, ["run", "--dataset", str(dataset_root), "--model", "not_a_model"]
    )
    assert result.exit_code == 2
    assert (
        "invalid configuration" in result.stderr.lower() or "invalid" in result.stderr
    )


def test_missing_dataset_exits_one(fake_embedder_override, tmp_path):
    result = cli_runner.invoke(
        app,
        ["run", "--dataset", str(tmp_path / "nope"), "--output", str(tmp_path / "out")],
    )
    assert result.exit_code == 1


def test_report_missing_results_exits_one(fake_embedder_override, tmp_path):
    result = cli_runner.invoke(app, ["report", "--output", str(tmp_path / "out")])
    assert result.exit_code == 1


def test_seed_flag_is_respected(fake_embedder_override, dataset_factory, tmp_path):
    dataset_root = _make_cli_dataset(dataset_factory)
    result = cli_runner.invoke(
        app,
        [
            "run",
            "--dataset",
            str(dataset_root),
            "--seed",
            "7",
            "--output",
            str(tmp_path / "out"),
        ],
    )
    assert result.exit_code == 0, result.stderr
    summary = json.loads(
        (tmp_path / "out" / "run_summary.json").read_text(encoding="utf-8")
    )
    assert summary["random_seed"] == 7
