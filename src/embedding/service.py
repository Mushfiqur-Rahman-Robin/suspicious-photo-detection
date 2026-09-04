"""Cache-aware embedding extraction service (SPEC §13, ED-6).

The service owns the cache lifecycle: it derives keys from content hashes,
consults the cache before encoding, batch-encodes only the misses, and stores
the results. Decoding and byte-reading are injected callables from `io` so
this module never touches the filesystem and the boundaries in
ARCHITECTURE §4 stay intact.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from core.entities import Embedding, ImageRecord
from core.exceptions import CacheError
from observability.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable

    import numpy as np
    from PIL import Image

    from core.ports import Embedder
    from io_layer.embedding_cache import EmbeddingCache

    DecodeImage = Callable[[ImageRecord], Image.Image]


class EmbeddingService:
    """Extracts L2-normalized embeddings through the Embedder port, cached.

    ``cache_only=True`` enforces the ``spd detect`` contract of reading only
    from cache (SPEC §5.10): any miss raises a ``CacheError`` telling the
    user to run ``spd embed`` first, so detection can never silently differ
    from the embedded state.
    """

    def __init__(
        self,
        embedder: Embedder,
        cache: EmbeddingCache,
        decode_image: DecodeImage,
    ) -> None:
        """Wire the embedder port, the content-addressed cache, and the decoder."""
        self._embedder = embedder
        self._cache = cache
        self._decode_image = decode_image
        self._logger = get_logger("embedding_service")
        self.hit_count = 0
        self.miss_count = 0

    @property
    def embedder(self) -> Embedder:
        """The underlying model adapter (for KPI/logs)."""
        return self._embedder

    def embed_records(
        self,
        records: Sequence[ImageRecord],
        cache_only: bool = False,
    ) -> list[Embedding]:
        """Return one Embedding per record, in order, consulting the cache.

        Cache hits reuse the stored vector; misses are decoded, batch-encoded,
        normalized, and stored. With ``cache_only`` any miss raises
        ``CacheError`` instead of computing.
        """
        keys = [
            self._cache.key(
                record.content_hash,
                self._embedder.model_name,
                self._embedder.model_version,
            )
            for record in records
        ]
        vectors_by_key: dict[str, np.ndarray] = {}
        miss_indices: list[int] = []
        for index, key in enumerate(keys):
            vector = self._cache.get(key)
            if vector is not None:
                vectors_by_key[key] = vector
                self.hit_count += 1
            else:
                miss_indices.append(index)

        if miss_indices:
            if cache_only:
                raise CacheError(
                    f"{len(miss_indices)} embedding(s) missing from cache "
                    f"(e.g. {records[miss_indices[0]].file_name}); run `spd embed` first"
                )
            self._encode_misses(records, keys, miss_indices, vectors_by_key)

        return [
            Embedding(
                vector=vectors_by_key[keys[index]],
                model=self._embedder.model_name,
                model_version=self._embedder.model_version,
                content_hash=record.content_hash,
                dim=self._embedder.dim,
            )
            for index, record in enumerate(records)
        ]

    def _encode_misses(
        self,
        records: Sequence[ImageRecord],
        keys: list[str],
        miss_indices: list[int],
        vectors_by_key: dict[str, np.ndarray],
    ) -> None:
        """Decode + encode the cache-miss records and store their vectors."""
        miss_images = [self._decode_image(records[index]) for index in miss_indices]
        encoded = self._embedder.embed_images(miss_images)
        for offset, index in enumerate(miss_indices):
            key = keys[index]
            vectors_by_key[key] = encoded[offset]
            self._cache.put(key, encoded[offset])
            self.miss_count += 1
        self._logger.info(
            "embeddings_computed",
            count=len(miss_indices),
            model=self._embedder.model_name,
            model_version=self._embedder.model_version,
        )
