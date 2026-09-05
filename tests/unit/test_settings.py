"""Unit tests: configuration validation and loading (SPEC §18, P0.2)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from config.settings import (
    DeviceKind,
    EmbeddingModel,
    LogLevel,
    Settings,
    load_settings,
)
from core.exceptions import ConfigurationError


def test_defaults_match_spec_catalog(make_settings):
    settings = make_settings()
    assert settings.embedding_model is EmbeddingModel.DINO_V2_SMALL
    assert settings.embedding_dim == 384
    assert settings.device is DeviceKind.AUTO
    assert settings.random_seed == 42
    assert settings.k_neighbors == 5
    assert settings.mad_k == 3.0
    assert settings.score_floor == 0.5
    assert settings.min_images_per_outlet == 2
    assert settings.ignore_corrupt_images is False
    assert settings.score_decimals == 4
    assert settings.batch_size == 32
    assert settings.centroid_weight == pytest.approx(1 / 3)


def test_output_filename_defaults_are_centralized(make_settings):
    settings = make_settings()
    assert settings.results_json_filename == "results.json"
    assert settings.results_csv_filename == "results.csv"
    assert settings.run_summary_filename == "run_summary.json"
    assert settings.write_up_filename == "write_up.md"
    assert settings.log_filename == "spd.log"
    assert settings.evaluation_filename == "evaluation.md"


def test_output_filenames_are_overrideable(make_settings):
    settings = make_settings(results_json_filename="out.json", log_filename="run.log")
    assert settings.results_json_filename == "out.json"
    assert settings.log_filename == "run.log"


def test_fusion_weights_must_sum_to_one(make_settings):
    with pytest.raises(ValidationError):
        make_settings(centroid_weight=0.5, knn_weight=0.5, isolation_forest_weight=0.1)


def test_min_images_per_outlet_must_be_at_least_two(make_settings):
    with pytest.raises(ValidationError):
        make_settings(min_images_per_outlet=1)


def test_unknown_environment_variable_is_rejected(make_settings, monkeypatch):
    monkeypatch.setenv("EMBEDDING_MODEL", "not_a_model")
    with pytest.raises(ValidationError):
        Settings()


def test_env_override_wins_over_default(monkeypatch):
    monkeypatch.setenv("RANDOM_SEED", "7")
    settings = Settings()
    assert settings.random_seed == 7


def test_load_settings_from_json_config(tmp_path, make_settings):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"random_seed": 123, "mad_k": 4.0}))
    settings = load_settings(config_path)
    assert settings.random_seed == 123
    assert settings.mad_k == 4.0


def test_load_settings_cli_flag_overrides_json(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"random_seed": 123}))
    settings = load_settings(config_path, random_seed=9)
    assert settings.random_seed == 9


def test_load_settings_missing_config_file_raises():
    with pytest.raises(ConfigurationError):
        load_settings(Path("/does/not/exist.json"))


def test_load_settings_invalid_json_raises(tmp_path):
    config_path = tmp_path / "bad.json"
    config_path.write_text("{not json")
    with pytest.raises(ConfigurationError):
        load_settings(config_path)


def test_load_settings_unknown_field_raises(tmp_path):
    config_path = tmp_path / "unknown.json"
    config_path.write_text(json.dumps({"not_a_field": 1}))
    with pytest.raises(ConfigurationError):
        load_settings(config_path)


def test_log_level_enum_is_bounded():
    assert LogLevel.DEBUG.value == "DEBUG"
    with pytest.raises(ValidationError):
        Settings(log_level="VERBOSE")


def test_fusion_weights_helper(make_settings):
    settings = make_settings()
    weights = settings.fusion_weights()
    assert weights == pytest.approx((1 / 3, 1 / 3, 1 / 3))
