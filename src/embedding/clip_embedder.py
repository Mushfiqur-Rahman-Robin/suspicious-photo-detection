"""CLIP embedder - the alternate embedding backend (ED-1).

Swapped in purely by config; because ``open_clip_torch`` is an optional extra
outside the locked core environment (SPEC §13), the backend is imported
lazily so the default DINOv2 path never pays for it and a CLIP run fails with
a clear, actionable error when the extra is missing.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from typing import Any

import numpy as np
import torch
from PIL import Image

from core.exceptions import ConfigurationError, EmbeddingError
from embedding.normalize import l2_normalize

CLIP_MODEL_NAME = "ViT-B-32"
CLIP_PRETRAINED = "laion2b_s34b_b79k"


class ClipEmbedder:
    """Encodes PIL images into L2-normalized CLIP ViT-B/32 embeddings.

    Only instantiated when ``EMBEDDING_MODEL=clip`` is configured; the
    ``open_clip`` module is resolved lazily so importing this module never
    fails on a DINOv2-only installation.
    """

    def __init__(self, device: torch.device, batch_size: int) -> None:
        """Load the CLIP backend and keep device + batch size for inference."""
        self._device = device
        self._batch_size = batch_size
        self._model, self._preprocess, self._backend_version = self._load_backend()
        self._per_image_latency_seconds: list[float] = []

    @property
    def model_name(self) -> str:
        """Canonical model name used in cache keys (ED-6)."""
        return "clip"

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
        """Backend version + weights pin; part of the cache-key namespace."""
        return f"{self._backend_version}:{CLIP_MODEL_NAME}:{CLIP_PRETRAINED}"

    @property
    def dim(self) -> int:
        """Embedding dimension for CLIP ViT-B/32."""
        return 512

    def embed_images(self, images: Sequence[Image.Image]) -> np.ndarray:
        """Encode ``images`` into an (N, 512) L2-normalized float32 array."""
        preprocessed = torch.stack([self._preprocess(image) for image in images])
        vectors: list[torch.Tensor] = []
        with torch.inference_mode():
            for start in range(0, preprocessed.shape[0], self._batch_size):
                batch = preprocessed[start : start + self._batch_size].to(self._device)
                batch_size = batch.shape[0]
                batch_started_at = time.perf_counter()
                try:
                    output = self._model.encode_image(batch)
                except Exception as exc:
                    raise EmbeddingError(f"CLIP inference failed: {exc}") from exc
                batch_elapsed = time.perf_counter() - batch_started_at
                self._per_image_latency_seconds.extend(
                    [batch_elapsed / batch_size] * batch_size
                )
                vectors.append(output)
        stacked = torch.cat(vectors, dim=0).float().cpu().numpy()
        return l2_normalize(stacked)

    def _load_backend(self) -> tuple[Any, Any, str]:
        """Import open_clip lazily and build the model + preprocessing.

        ``open_clip`` is an optional dependency outside the locked core
        environment (SPEC §13); the dynamic import keeps the DINOv2-only path
        free of it and produces a clear ConfigurationError when a CLIP run is
        attempted without the extra installed.
        """
        try:
            import open_clip  # type: ignore[import-not-found]
        except ImportError as exc:
            raise ConfigurationError(
                "CLIP backend requires the optional `clip` extra; install with "
                "`pip install 'suspicious-photo-detection[clip]'` and pin a "
                "lockfile for it (SPEC §13)"
            ) from exc
        open_clip_module: Any = open_clip
        model, _, preprocess = open_clip_module.create_model_and_transforms(
            CLIP_MODEL_NAME,
            pretrained=CLIP_PRETRAINED,
        )
        version = getattr(open_clip, "__version__", "unknown")
        return model.to(self._device), preprocess, version
