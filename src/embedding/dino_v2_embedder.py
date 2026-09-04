"""DINOv2 ViT-S/14 embedder - the default embedding backend (ED-1).

DINOv2 was removed from torchvision 0.29, so the official weights are loaded
through ``torch.hub`` pinned to a fixed commit SHA. The pinned SHA is the
``model_version`` and therefore part of the embedding-cache key namespace
(ED-6), guaranteeing that a different weight snapshot can never mix with
another. Preprocessing follows the canonical DINOv2 evaluation pipeline:
resize short side to 256, center-crop 224, ImageNet normalization.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from typing import TYPE_CHECKING, cast

import numpy as np
import torch
from PIL import Image
from torchvision import transforms  # type: ignore[import-untyped]

from core.exceptions import EmbeddingError
from embedding.normalize import l2_normalize

if TYPE_CHECKING:
    import torch.nn as nn

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]
DINO_V2_INPUT_SIZE = 224
DINO_V2_CLASS_TOKEN_DIM = 384

DINO_V2_EVAL_TRANSFORM = transforms.Compose(
    [
        transforms.Resize(256),
        transforms.CenterCrop(DINO_V2_INPUT_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ]
)


class DinoV2Embedder:
    """Encodes PIL images into L2-normalized 384-dim DINOv2 embeddings.

    Inference-only: the model runs in ``eval()`` mode under ``torch.no_grad()``
    and inputs are processed in configurable batches (SPEC §10.1, §15).
    """

    def __init__(
        self,
        device: torch.device,
        batch_size: int,
        hub_repo: str,
        hub_ref: str,
        model: nn.Module | None = None,
    ) -> None:
        """Load DINOv2 ViT-S/14 (or accept an injected stub for tests) and set eval mode."""
        self._device = device
        self._batch_size = batch_size
        self._hub_repo = hub_repo
        self._hub_ref = hub_ref
        self._model = model if model is not None else self._load_backend()
        self._model.to(device)
        self._model.eval()
        self._per_image_latency_seconds: list[float] = []

    @property
    def model_name(self) -> str:
        """Canonical model name used in cache keys (ED-6)."""
        return "dino_v2_small"

    @property
    def per_image_latency_seconds(self) -> list[float]:
        """Per-image inference latency (sec) from the batches encoded so far.

        One sample per image, derived as ``batch wall time / batch size`` so a
        batch of ``N`` images contributes ``N`` samples. Used to compute the
        p50/p95/p99 KPIs in the run summary (SPEC §14). Not part of the
        ``Embedder`` port: test fakes simply omit it.
        """
        return list(self._per_image_latency_seconds)

    @property
    def model_version(self) -> str:
        """Pinned hub commit SHA; part of the cache-key namespace."""
        return self._hub_ref

    @property
    def dim(self) -> int:
        """Embedding dimension (384 for DINOv2 ViT-S/14)."""
        return DINO_V2_CLASS_TOKEN_DIM

    def embed_images(self, images: Sequence[Image.Image]) -> np.ndarray:
        """Encode ``images`` into an (N, 384) L2-normalized float32 array.

        Raises ``EmbeddingError`` if inference fails so the failure is
        attributed to the embedding stage rather than surfacing as raw torch.
        """
        tensors = torch.stack(
            [cast(torch.Tensor, DINO_V2_EVAL_TRANSFORM(image)) for image in images]
        )
        vectors: list[torch.Tensor] = []
        with torch.inference_mode():
            for start in range(0, tensors.shape[0], self._batch_size):
                batch = tensors[start : start + self._batch_size].to(self._device)
                batch_size = batch.shape[0]
                batch_started_at = time.perf_counter()
                try:
                    output = self._model(batch)
                except Exception as exc:
                    raise EmbeddingError(f"DINOv2 inference failed: {exc}") from exc
                batch_elapsed = time.perf_counter() - batch_started_at
                self._per_image_latency_seconds.extend(
                    [batch_elapsed / batch_size] * batch_size
                )
                vectors.append(output.detach().cpu())
        stacked = torch.cat(vectors, dim=0).numpy().astype(np.float32)
        return l2_normalize(stacked)

    def _load_backend(self) -> nn.Module:
        """Load the pinned DINOv2 ViT-S/14 weights via torch.hub (cached)."""
        try:
            repo = f"{self._hub_repo}:{self._hub_ref}"
            model = torch.hub.load(  # type: ignore[no-untyped-call]
                repo,
                "dinov2_vits14",
                trust_repo=True,  # pyright: ignore[reportArgumentType]
                pretrained=True,
            )
        except Exception as exc:
            raise EmbeddingError(
                "unable to load DINOv2 ViT-S/14 weights "
                f"(repo={self._hub_repo}, ref={self._hub_ref}): {exc}"
            ) from exc
        if not isinstance(model, torch.nn.Module):
            raise EmbeddingError("DINOv2 hub entrypoint did not return a torch module")
        return model
