"""Unit tests: ports, detector factory, and logging (SPEC §19, P1.2/P3.2)."""

from __future__ import annotations

import numpy as np

from config.settings import Settings
from conftest import PixelMeanEmbedder
from core.ports import Embedder, OutlierDetector, ResultWriter
from detection.ensemble_detector import EnsembleDetector
from detection.factory import create_detector
from io_layer.result_writer import ResultWriter as ConcreteResultWriter
from observability.logging import (
    bind_run_context,
    clear_run_context,
    configure_logging,
    get_logger,
)


def test_pixel_mean_embedder_satisfies_embedder_port():
    assert isinstance(PixelMeanEmbedder(), Embedder)


def test_ensemble_detector_satisfies_detector_port():
    assert isinstance(EnsembleDetector(Settings()), OutlierDetector)


def test_concrete_writer_satisfies_writer_port():
    assert isinstance(ConcreteResultWriter(), ResultWriter)


def test_create_detector_default_is_ensemble():
    assert isinstance(create_detector(Settings()), EnsembleDetector)


def test_create_detector_unknown_name_raises():
    import pytest

    from core.exceptions import ConfigurationError

    with pytest.raises(ConfigurationError):
        create_detector(Settings(), detector_name="lof")


def test_configure_logging_and_logger_work():
    configure_logging(Settings().log_level)
    logger = get_logger("test")
    assert logger is not None


def test_configure_logging_writes_structured_log_file(tmp_path):
    configure_logging(Settings().log_level, log_dir=tmp_path)
    get_logger("test").info("log_file_probe", probe="value")
    log_path = tmp_path / "spd.log"
    assert log_path.is_file()
    line = log_path.read_text(encoding="utf-8").strip()
    assert '"event": "log_file_probe"' in line
    assert '"probe": "value"' in line


def test_run_context_binding_and_clearing():
    bind_run_context(run_id="abc", outlet_id="o1")
    clear_run_context()
    bind_run_context(stage="load")
    clear_run_context()


def test_fake_embedder_produces_normalized_vectors():
    from PIL import Image

    images = [Image.new("RGB", (8, 8), (255, 0, 0))]
    vectors = PixelMeanEmbedder().embed_images(images)
    assert vectors.shape == (1, 3)
    assert np.linalg.norm(vectors[0]) == 1.0
