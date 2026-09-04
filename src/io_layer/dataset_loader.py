"""Dataset discovery and loading (SPEC §5.1, FR1).

One immediate-child directory = one outlet; every supported image file in it
is an ``ImageRecord`` with a content hash. Ordering is deterministic (sorted
by outlet id and file name) so results never depend on traversal order.
Corrupt images fail the run unless ``ignore_corrupt_images`` is set.
"""

from __future__ import annotations

from pathlib import Path

from core.entities import ImageRecord, Outlet
from core.exceptions import CorruptImageError
from observability.logging import get_logger

from .image_utils import (
    SUPPORTED_IMAGE_EXTENSIONS,
    compute_content_hash,
    decode_image_from_path,
    read_image_bytes,
)


class DatasetLoader:
    """Discovers outlets and their image records under a dataset root.

    The loader performs decode validation and content hashing at discovery
    time (FR1) so corrupt files surface immediately with a clear error and so
    the embedding stage can key the cache without re-reading bytes.
    """

    def __init__(
        self,
        min_images_per_outlet: int,
        ignore_corrupt_images: bool,
        max_image_dimension: int,
        max_image_pixels: int,
    ) -> None:
        """Configure discovery policy (minimum size, corrupt-image handling, bounds)."""
        self._min_images_per_outlet = min_images_per_outlet
        self._ignore_corrupt_images = ignore_corrupt_images
        self._max_image_dimension = max_image_dimension
        self._max_image_pixels = max_image_pixels
        self._logger = get_logger("dataset_loader")

    def discover_outlets(self, dataset_root: Path) -> list[Outlet]:
        """Return every outlet under ``dataset_root`` with its image records.

        Immediate children that are directories are outlets; inside each, only
        files with a supported extension are images (SPEC §5.1). A corrupt
        image raises ``CorruptImageError`` unless the ignore policy is set,
        in which case it is skipped and logged as a warning.
        """
        if not dataset_root.is_dir():
            raise FileNotFoundError(f"dataset root does not exist: {dataset_root}")

        outlets: list[Outlet] = []
        for folder in sorted(dataset_root.iterdir()):
            if not folder.is_dir():
                continue
            outlet = Outlet(outlet_id=folder.name)
            outlet.images = self._discover_images(folder)
            outlets.append(outlet)
        return outlets

    def _discover_images(self, outlet_folder: Path) -> list[ImageRecord]:
        """Collect valid, decode-checked ImageRecords for one outlet folder."""
        records: list[ImageRecord] = []
        for file_path in sorted(outlet_folder.iterdir()):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
                continue
            try:
                image_bytes = read_image_bytes(file_path)
                decode_image_from_path(
                    file_path,
                    self._max_image_dimension,
                    self._max_image_pixels,
                )
            except CorruptImageError as exc:
                if self._ignore_corrupt_images:
                    self._logger.warning(
                        "corrupt_image_skipped",
                        outlet_id=exc.outlet_id,
                        file_name=exc.file_name,
                        cause=str(exc),
                    )
                    continue
                raise
            records.append(
                ImageRecord(
                    file_name=file_path.name,
                    path=file_path,
                    content_hash=compute_content_hash(image_bytes),
                )
            )
        if len(records) < self._min_images_per_outlet:
            self._logger.warning(
                "outlet_below_min_images",
                outlet_id=outlet_folder.name,
                image_count=len(records),
                min_images_per_outlet=self._min_images_per_outlet,
            )
        return records
