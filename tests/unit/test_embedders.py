"""Unit tests: embedder adapters + factory (SPEC §10.1, ED-1, P1.5/P1.6)."""

from __future__ import annotations

import importlib.util

import numpy as np
import pytest
import torch
from PIL import Image


def _module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


from config.settings import EmbeddingModel, Settings
from core.exceptions import ConfigurationError, EmbeddingError
from embedding import factory
from embedding.clip_embedder import ClipEmbedder
from embedding.dino_v2_embedder import DINO_V2_CLASS_TOKEN_DIM, DinoV2Embedder
from embedding.normalize import l2_normalize


class StubBackbone(torch.nn.Module):
    """Deterministic stub returning a fixed 384-dim vector per image."""

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        image_count = x.shape[0]
        return torch.stack(
            [
                torch.full((DINO_V2_CLASS_TOKEN_DIM,), float(index + 1))
                for index in range(image_count)
            ]
        )


def _sample_images(count: int = 3) -> list[Image.Image]:
    return [
        Image.new("RGB", (300, 400), (index * 10 + 5, 20, 30)) for index in range(count)
    ]


def _stub_embedder(batch_size: int = 2) -> DinoV2Embedder:
    return DinoV2Embedder(
        device=torch.device("cpu"),
        batch_size=batch_size,
        hub_repo="facebookresearch/dinov2",
        hub_ref="pinned-sha",
        model=StubBackbone(),
    )


def test_dino_embedder_identity_fields():
    embedder = _stub_embedder()
    assert embedder.model_name == "dino_v2_small"
    assert embedder.model_version == "pinned-sha"
    assert embedder.dim == 384


def test_dino_embed_images_shape_and_normalization():
    embedder = _stub_embedder()
    images = _sample_images()
    vectors = embedder.embed_images(images)
    assert vectors.shape == (len(images), 384)
    np.testing.assert_allclose(
        np.linalg.norm(vectors, axis=1), np.ones(len(images)), atol=1e-5
    )


def test_dino_embed_images_is_deterministic():
    embedder = _stub_embedder()
    images = _sample_images()
    first = embedder.embed_images(images)
    second = embedder.embed_images(images)
    np.testing.assert_array_equal(first, second)


def test_dino_embed_images_batch_size_does_not_change_result():
    images = _sample_images()
    batched = _stub_embedder(batch_size=2).embed_images(images)
    unbatched = _stub_embedder(batch_size=100).embed_images(images)
    np.testing.assert_array_equal(batched, unbatched)


def test_dino_embed_images_returns_l2_normalized_rows():
    embedder = _stub_embedder()
    raw = StubBackbone()(torch.zeros(3, 3, 224, 224))
    expected = l2_normalize(raw.numpy().astype(np.float32))
    vectors = embedder.embed_images(_sample_images())
    np.testing.assert_allclose(vectors, expected)


def test_dino_inference_failure_is_wrapped(monkeypatch):
    class BrokenBackbone(torch.nn.Module):
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            raise RuntimeError("gpu exploded")

    embedder = DinoV2Embedder(
        device=torch.device("cpu"),
        batch_size=2,
        hub_repo="repo",
        hub_ref="ref",
        model=BrokenBackbone(),
    )
    with pytest.raises(EmbeddingError):
        embedder.embed_images(_sample_images())


def test_dino_load_backend_wraps_hub_failure(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("no network")

    monkeypatch.setattr(torch.hub, "load", boom)
    with pytest.raises(EmbeddingError):
        DinoV2Embedder(
            device=torch.device("cpu"),
            batch_size=2,
            hub_repo="facebookresearch/dinov2",
            hub_ref="pinned-sha",
        )


def test_dino_load_backend_rejects_non_module(monkeypatch):
    monkeypatch.setattr(torch.hub, "load", lambda *args, **kwargs: "not a module")
    with pytest.raises(EmbeddingError):
        DinoV2Embedder(
            device=torch.device("cpu"),
            batch_size=2,
            hub_repo="facebookresearch/dinov2",
            hub_ref="pinned-sha",
        )


@pytest.mark.skipif(
    _module_available("open_clip"),
    reason="open_clip installed in this environment, so the missing-extra path is untestable",
)
def test_clip_embedder_requires_optional_extra():
    with pytest.raises(ConfigurationError):
        ClipEmbedder(device=torch.device("cpu"), batch_size=2)


def test_clip_identity_fields_without_backend(monkeypatch):
    import sys

    monkeypatch.setitem(sys.modules, "open_clip", None)
    with pytest.raises(ConfigurationError):
        ClipEmbedder(device=torch.device("cpu"), batch_size=2)


def test_factory_dispatches_dino(monkeypatch):
    captured = {}

    class Dummy:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(factory, "DinoV2Embedder", Dummy)
    result = factory.create_embedder(Settings())
    assert isinstance(result, Dummy)
    assert captured["batch_size"] == 32
    assert captured["hub_ref"] == Settings().dino_v2_hub_ref


def test_factory_dispatches_clip(monkeypatch):
    class Dummy:
        def __init__(self, device, batch_size):
            self.batch_size = batch_size

    monkeypatch.setattr(factory, "ClipEmbedder", Dummy)
    settings = Settings(embedding_model=EmbeddingModel.CLIP)
    result = factory.create_embedder(settings)
    assert result.batch_size == 32


def test_factory_rejects_unknown_model(make_settings):
    with pytest.raises(ConfigurationError):
        factory.create_embedder(Settings(), model_name="bogus")  # type: ignore[arg-type]


def _module_available(module_name: str) -> bool:
    import importlib.util

    return importlib.util.find_spec(module_name) is not None
