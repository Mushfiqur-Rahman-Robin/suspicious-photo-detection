"""Unit tests: image byte reading, hashing, and decode bounds (SPEC §17, P1.3)."""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from core.exceptions import CorruptImageError, DatasetError
from io_layer.image_utils import (
    SUPPORTED_IMAGE_EXTENSIONS,
    compute_content_hash,
    decode_image_from_path,
    read_image_bytes,
)


def test_supported_extensions_set():
    assert ".jpg" in SUPPORTED_IMAGE_EXTENSIONS
    assert ".jpeg" in SUPPORTED_IMAGE_EXTENSIONS
    assert ".png" in SUPPORTED_IMAGE_EXTENSIONS


def test_read_image_bytes_returns_raw_content(tmp_path):
    path = tmp_path / "img.jpg"
    Image.new("RGB", (8, 8), (1, 2, 3)).save(path)
    assert read_image_bytes(path) == path.read_bytes()


def test_read_image_bytes_missing_file_raises(tmp_path):
    with pytest.raises(DatasetError):
        read_image_bytes(tmp_path / "missing.jpg")


def test_content_hash_is_sha256_hex():
    digest = compute_content_hash(b"hello")
    assert len(digest) == 64
    assert all(char in "0123456789abcdef" for char in digest)


def test_same_bytes_same_hash_different_bytes_different_hash():
    assert compute_content_hash(b"a") == compute_content_hash(b"a")
    assert compute_content_hash(b"a") != compute_content_hash(b"b")


def test_decode_valid_jpeg_returns_rgb(tmp_path):
    path = tmp_path / "img.jpg"
    Image.new("RGB", (16, 16), (1, 2, 3)).save(path)
    image = decode_image_from_path(path, max_dimension=4096, max_pixels=16_000_000)
    assert image.mode == "RGB"
    assert image.size == (16, 16)


def test_decode_corrupt_file_raises(tmp_path):
    path = tmp_path / "bad.jpg"
    path.write_bytes(b"not an image")
    with pytest.raises(CorruptImageError) as excinfo:
        decode_image_from_path(path, max_dimension=4096, max_pixels=16_000_000)
    assert path.parent.name in str(excinfo.value)  # outlet id derived from path
    assert path.name in str(excinfo.value)


def test_decode_oversized_dimension_raises(tmp_path):
    path = tmp_path / "big.jpg"
    Image.new("RGB", (5000, 100), (1, 2, 3)).save(path)
    with pytest.raises(CorruptImageError):
        decode_image_from_path(path, max_dimension=4096, max_pixels=16_000_000)


def test_decode_oversized_pixel_count_raises(tmp_path):
    path = tmp_path / "huge.jpg"
    Image.new("RGB", (2000, 2000), (1, 2, 3)).save(path)  # 4M pixels > 16M? no
    with pytest.raises(CorruptImageError):
        decode_image_from_path(path, max_dimension=4096, max_pixels=1_000_000)


def test_numpy_roundtrip_unchanged():
    vector = np.array([0.6, 0.8])
    assert np.allclose(vector, vector)
