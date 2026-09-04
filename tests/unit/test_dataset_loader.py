"""Unit tests: dataset discovery/loading (SPEC §5.1, FR1, P1.3)."""

from __future__ import annotations

import pytest

from core.exceptions import CorruptImageError
from io_layer.dataset_loader import DatasetLoader


def _make_loader(ignore_corrupt_images: bool = False) -> DatasetLoader:
    return DatasetLoader(
        min_images_per_outlet=2,
        ignore_corrupt_images=ignore_corrupt_images,
        max_image_dimension=4096,
        max_image_pixels=16_000_000,
    )


def test_discovers_outlets_sorted_and_deterministic(dataset_factory):
    root = dataset_factory(
        {
            "outlet_b": {"b1.jpg": (10, 10, 10), "b2.jpg": (20, 20, 20)},
            "outlet_a": {"a1.jpg": (30, 30, 30), "a2.jpg": (40, 40, 40)},
        }
    )
    outlets = _make_loader().discover_outlets(root)
    assert [outlet.outlet_id for outlet in outlets] == ["outlet_a", "outlet_b"]
    assert [record.file_name for record in outlets[0].images] == ["a1.jpg", "a2.jpg"]


def test_non_directory_children_are_ignored(dataset_factory, tmp_path):
    root = dataset_factory({"outlet_a": {"a1.jpg": (1, 1, 1), "a2.jpg": (2, 2, 2)}})
    (root / "not_a_folder.txt").write_text("ignore me")
    outlets = _make_loader().discover_outlets(root)
    assert [outlet.outlet_id for outlet in outlets] == ["outlet_a"]


def test_unsupported_extensions_are_ignored(dataset_factory):
    root = dataset_factory({"outlet_a": {"a1.jpg": (1, 1, 1), "a2.jpeg": (2, 2, 2)}})
    (root / "outlet_a" / "notes.txt").write_text("not an image")
    outlets = _make_loader().discover_outlets(root)
    assert [record.file_name for record in outlets[0].images] == ["a1.jpg", "a2.jpeg"]


def test_content_hash_is_sha256_of_bytes(dataset_factory):
    root = dataset_factory({"outlet_a": {"a1.jpg": (1, 1, 1), "a2.jpg": (2, 2, 2)}})
    record = _make_loader().discover_outlets(root)[0].images[0]
    assert len(record.content_hash) == 64  # sha256 hex digest


def test_same_content_yields_same_hash(dataset_factory):
    root = dataset_factory({"outlet_a": {"a1.jpg": (5, 5, 5), "a2.jpg": (5, 5, 5)}})
    records = _make_loader().discover_outlets(root)[0].images
    assert records[0].content_hash == records[1].content_hash


def test_corrupt_image_fails_run_by_default(dataset_factory):
    root = dataset_factory({"outlet_a": {"a1.jpg": (1, 1, 1), "a2.jpg": (2, 2, 2)}})
    (root / "outlet_a" / "bad.jpg").write_bytes(b"not an image at all")
    with pytest.raises(CorruptImageError):
        _make_loader().discover_outlets(root)


def test_corrupt_image_skipped_when_ignored(dataset_factory):
    root = dataset_factory({"outlet_a": {"a1.jpg": (1, 1, 1), "a2.jpg": (2, 2, 2)}})
    (root / "outlet_a" / "bad.jpg").write_bytes(b"not an image at all")
    outlets = _make_loader(ignore_corrupt_images=True).discover_outlets(root)
    assert [record.file_name for record in outlets[0].images] == ["a1.jpg", "a2.jpg"]


def test_oversized_image_fails_bounds_check(dataset_factory):
    root = dataset_factory({"outlet_a": {"a1.jpg": (1, 1, 1), "a2.jpg": (2, 2, 2)}})
    from PIL import Image

    Image.new("RGB", (5000, 5000), (1, 1, 1)).save(root / "outlet_a" / "huge.jpg")
    with pytest.raises(CorruptImageError):
        _make_loader().discover_outlets(root)


def test_missing_dataset_root_raises(tmp_path):
    import pytest

    with pytest.raises(FileNotFoundError):
        _make_loader().discover_outlets(tmp_path / "does_not_exist")


def pytest_raises_corrupt():
    import pytest

    return pytest.raises(CorruptImageError)
