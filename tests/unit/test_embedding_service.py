"""Unit tests: cache-aware embedding service (SPEC §13, ED-6, P1.4/P1.5)."""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from config.settings import Settings
from core.entities import ImageRecord
from core.exceptions import CacheError
from embedding.service import EmbeddingService
from io_layer.embedding_cache import EmbeddingCache
from io_layer.image_utils import compute_content_hash, decode_image_from_path


def _records(tmp_path, count: int = 3) -> list[ImageRecord]:
    records = []
    for index in range(count):
        path = tmp_path / f"img_{index}.jpg"
        Image.new("RGB", (16, 16), (index * 40 + 10, 10, 10)).save(path)
        records.append(
            ImageRecord(
                file_name=path.name,
                path=path,
                content_hash=compute_content_hash(path.read_bytes()),
            )
        )
    return records


def _service(tmp_path, settings=None):
    from conftest import PixelMeanEmbedder

    settings = settings or Settings(cache_dir=tmp_path / "cache")
    cache = EmbeddingCache(settings.cache_dir)
    service = EmbeddingService(
        embedder=PixelMeanEmbedder(),
        cache=cache,
        decode_image=lambda record: decode_image_from_path(
            record.path,
            settings.max_image_dimension,
            settings.max_image_pixels,
        ),
    )
    return service, cache


def test_embeddings_are_aligned_with_records(tmp_path):
    service, _ = _service(tmp_path)
    records = _records(tmp_path)
    embeddings = service.embed_records(records)
    assert [embedding.content_hash for embedding in embeddings] == [
        record.content_hash for record in records
    ]
    assert all(embedding.dim == 3 for embedding in embeddings)


def test_misses_are_cached_and_reused(tmp_path):
    service, cache = _service(tmp_path)
    records = _records(tmp_path)
    service.embed_records(records)
    assert service.miss_count == len(records)
    assert service.hit_count == 0

    keys = [
        cache.key(
            r.content_hash, service.embedder.model_name, service.embedder.model_version
        )
        for r in records
    ]
    assert all(cache.contains(key) for key in keys)

    service.embed_records(records)
    assert service.hit_count == len(records)
    assert service.miss_count == len(records)  # unchanged: nothing recomputed


def test_warm_and_cold_embeddings_are_identical(tmp_path):
    service, _ = _service(tmp_path)
    records = _records(tmp_path)
    cold = service.embed_records(records)
    warm = service.embed_records(records)
    for cold_vector, warm_vector in zip(cold, warm, strict=True):
        np.testing.assert_array_equal(cold_vector.vector, warm_vector.vector)


def test_cache_only_raises_on_miss(tmp_path):
    service, _ = _service(tmp_path)
    records = _records(tmp_path)
    with pytest.raises(CacheError):
        service.embed_records(records, cache_only=True)


def test_cache_only_succeeds_after_warm(tmp_path):
    service, _ = _service(tmp_path)
    records = _records(tmp_path)
    service.embed_records(records)
    embeddings = service.embed_records(records, cache_only=True)
    assert len(embeddings) == len(records)


def test_empty_records_return_empty(tmp_path):
    service, _ = _service(tmp_path)
    assert service.embed_records([]) == []


def test_service_exposes_empty_latency_without_real_embedder(tmp_path):
    """Fakes implementing only the Embedder port yield no latency KPIs."""
    service, _ = _service(tmp_path)
    service.embed_records(_records(tmp_path))
    assert service.embedding_latency_seconds == []
