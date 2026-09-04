"""Unit tests: content-addressed embedding cache (SPEC §13, ED-6, P1.4)."""

from __future__ import annotations

import numpy as np

from io_layer.embedding_cache import EmbeddingCache


def test_key_encodes_content_hash_model_and_version(tmp_path):
    cache = EmbeddingCache(tmp_path)
    key = cache.key("abc123", "dino_v2_small", "sha1")
    assert key == "dino_v2_small/sha1/abc123.npy"


def test_put_then_get_roundtrips_exactly(tmp_path):
    cache = EmbeddingCache(tmp_path)
    key = cache.key("abc", "model", "v1")
    vector = np.array([0.6, 0.8], dtype=np.float32)
    cache.put(key, vector)
    loaded = cache.get(key)
    assert loaded is not None
    np.testing.assert_array_equal(loaded, vector)


def test_get_returns_none_on_miss(tmp_path):
    cache = EmbeddingCache(tmp_path)
    assert cache.get(cache.key("missing", "model", "v1")) is None


def test_different_model_namespace_is_distinct(tmp_path):
    cache = EmbeddingCache(tmp_path)
    key_a = cache.key("abc", "model_a", "v1")
    key_b = cache.key("abc", "model_b", "v1")
    cache.put(key_a, np.array([1.0, 0.0]))
    assert cache.get(key_a) is not None
    assert cache.get(key_b) is None


def test_different_model_version_is_distinct(tmp_path):
    cache = EmbeddingCache(tmp_path)
    cache.put(cache.key("abc", "model", "v1"), np.array([1.0, 0.0]))
    assert cache.get(cache.key("abc", "model", "v2")) is None


def test_corrupt_cache_entry_treated_as_miss(tmp_path):
    cache = EmbeddingCache(tmp_path)
    key = cache.key("abc", "model", "v1")
    target = tmp_path / key
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"not a numpy file")
    assert cache.get(key) is None
    assert not target.exists()  # deleted to avoid poisoning future runs


def test_contains_reflects_disk_state(tmp_path):
    cache = EmbeddingCache(tmp_path)
    key = cache.key("abc", "model", "v1")
    assert not cache.contains(key)
    cache.put(key, np.array([1.0, 0.0]))
    assert cache.contains(key)
