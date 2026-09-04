"""Image byte reading, decoding, and corruption/bounds checks (SPEC §17).

The dataset is untrusted input: every image is decoded with bounds checks and
a corrupt or out-of-bounds file is rejected with a clear, structured error
instead of silently biasing the result (SPEC §5.1).

Note: the stdlib ``io`` module is not imported here because the flat ``src/io``
package would shadow it on ``sys.path`` (ARCHITECTURE §4); decoding always
happens from a ``Path`` via Pillow, which reads the file itself.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from core.exceptions import CorruptImageError, DatasetError

SUPPORTED_IMAGE_EXTENSIONS: frozenset[str] = frozenset({".jpg", ".jpeg", ".png"})


def read_image_bytes(path: Path) -> bytes:
    """Read the raw bytes of an image file, raising DatasetError on failure."""
    try:
        return path.read_bytes()
    except OSError as exc:
        raise DatasetError(f"unable to read image file {path}: {exc}") from exc


def compute_content_hash(image_bytes: bytes) -> str:
    """Return the sha256 hex digest of the decoded image bytes (ED-6)."""
    return hashlib.sha256(image_bytes).hexdigest()


def decode_image_from_path(
    path: Path,
    max_dimension: int,
    max_pixels: int,
) -> Image.Image:
    """Decode an image file into an RGB PIL image with bounds checks.

    Derives the outlet/file names from the path so corruption errors are
    immediately actionable. Raises ``CorruptImageError`` when the file is not
    a decodable image or when its dimensions exceed the configured
    untrusted-input bounds (decompression-bomb protection, SPEC §17).
    """
    outlet_id = path.parent.name
    file_name = path.name
    try:
        image = Image.open(path)
        image.load()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise CorruptImageError(
            outlet_id,
            file_name,
            f"not a decodable image: {exc}",
        ) from exc

    width, height = image.size
    if width <= 0 or height <= 0:
        raise CorruptImageError(outlet_id, file_name, "image has invalid dimensions")
    if width > max_dimension or height > max_dimension:
        raise CorruptImageError(
            outlet_id,
            file_name,
            f"dimension {width}x{height} exceeds configured max of {max_dimension}",
        )
    if width * height > max_pixels:
        raise CorruptImageError(
            outlet_id,
            file_name,
            f"pixel count {width * height} exceeds configured max of {max_pixels}",
        )
    return image.convert("RGB")
