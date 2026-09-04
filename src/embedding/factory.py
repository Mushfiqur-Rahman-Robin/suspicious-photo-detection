"""Embedder factory (Factory pattern, SPEC §19, ED-1).

Switching embedding models is a config change, never a code change: the
factory maps a model name to its adapter and resolves the configured device.
"""

from __future__ import annotations

from config.settings import EmbeddingModel, Settings
from core.exceptions import ConfigurationError
from core.ports import Embedder
from embedding.device import resolve_torch_device

from .clip_embedder import ClipEmbedder
from .dino_v2_embedder import DinoV2Embedder


def create_embedder(
    settings: Settings,
    model_name: EmbeddingModel | None = None,
) -> Embedder:
    """Instantiate the configured (or explicitly requested) embedding adapter."""
    name = model_name if model_name is not None else settings.embedding_model
    device = resolve_torch_device(settings.device)

    if name is EmbeddingModel.DINO_V2_SMALL:
        return DinoV2Embedder(
            device=device,
            batch_size=settings.batch_size,
            hub_repo=settings.dino_v2_hub_repo,
            hub_ref=settings.dino_v2_hub_ref,
        )
    if name is EmbeddingModel.CLIP:
        return ClipEmbedder(device=device, batch_size=settings.batch_size)
    raise ConfigurationError(f"unknown embedding model: {name}")
