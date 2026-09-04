"""Shared fixtures for the SPD test suite.

Fakes live here so no unit/integration test ever touches a real embedding
model (no downloads, fully deterministic). The ``PixelMeanEmbedder`` turns a
real image into a 3-dim L2-normalized mean-color vector, which lets end-to-end
tests prove the pipeline on genuine image bytes: a consistently colored outlet
plus an injected differently colored image is flaggable by geometry alone.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from config.settings import Settings
from embedding.normalize import l2_normalize
from pipeline.runner import PipelineRunner

RGB = tuple[int, int, int]


class PixelMeanEmbedder:
    """Test-only Embedder: L2-normalized per-channel mean color (3-dim)."""

    model_name = "test_pixel_mean"
    model_version = "test_v1"
    dim = 3

    def embed_images(self, images: list[Image.Image]) -> np.ndarray:
        vectors: list[np.ndarray] = []
        for image in images:
            small = image.convert("RGB").resize((8, 8))
            mean = np.asarray(small, dtype=np.float64).reshape(-1, 3).mean(axis=0)
            vectors.append(mean)
        return l2_normalize(np.asarray(vectors, dtype=np.float64))


class ConstantVectorEmbedder:
    """Test-only Embedder: returns a fixed unit vector regardless of input."""

    model_name = "test_constant"
    model_version = "test_v1"
    dim = 2

    def embed_images(self, images: list[Image.Image]) -> np.ndarray:
        return np.tile(np.array([1.0, 0.0]), (len(images), 1))


@pytest.fixture
def make_settings() -> Callable[..., Settings]:
    """Factory that builds validated, frozen Settings with arbitrary overrides."""

    def _make(**overrides: object) -> Settings:
        return Settings(**overrides)

    return _make


@pytest.fixture
def dataset_factory(tmp_path: Path) -> Callable[..., Path]:
    """Factory that materializes a synthetic image dataset on disk.

    Shape: ``{outlet_id: {file_name: (r, g, b)}}``; every image is a solid
    color, which makes the PixelMeanEmbedder's output fully deterministic.
    """

    def _make(outlets: dict[str, dict[str, RGB]]) -> Path:
        root = tmp_path / "dataset"
        for outlet_id, files in outlets.items():
            folder = root / outlet_id
            folder.mkdir(parents=True, exist_ok=True)
            for file_name, rgb in files.items():
                Image.new("RGB", (64, 64), rgb).save(folder / file_name)
        return root

    return _make


@pytest.fixture
def pixel_mean_embedder() -> PixelMeanEmbedder:
    """The deterministic pixel-mean embedder used across pipeline tests."""
    return PixelMeanEmbedder()


@pytest.fixture
def runner_factory(
    tmp_path: Path,
    pixel_mean_embedder: PixelMeanEmbedder,
) -> Callable[..., PipelineRunner]:
    """Factory that builds an isolated runner with the fake embedder injected."""

    def _make(**settings_overrides: object) -> PipelineRunner:
        settings = Settings(
            **{
                "cache_dir": tmp_path / "cache",
                "output_dir": tmp_path / "results",
                "log_dir": tmp_path / "logs",
                **settings_overrides,
            }
        )
        return PipelineRunner(settings, embedder=pixel_mean_embedder)

    return _make


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """A dedicated output directory per test."""
    return tmp_path / "results"


@pytest.fixture
def cache_dir(tmp_path: Path) -> Path:
    """A dedicated cache directory per test."""
    return tmp_path / "cache"
