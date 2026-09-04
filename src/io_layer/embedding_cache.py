"""Content-addressed embedding cache (SPEC §13, ED-6).

Key = sha256 of the decoded image bytes + model + model_version, so changing
the model or weights produces a fresh namespace and identical images always
map to identical vectors. Stored as ``.npy`` files, written atomically so an
interrupted ``spd embed`` never leaves a torn vector behind.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from observability.logging import get_logger


class EmbeddingCache:
    """Disk-backed store for L2-normalized embedding vectors.

    Transparency invariant (SPEC §13): a cold and a warm cache must yield
    byte-identical results, so ``get`` returns exactly what ``put`` stored and
    a corrupt entry is recomputed (deleted + treated as a miss) rather than
    silently trusted.
    """

    def __init__(self, cache_dir: Path) -> None:
        """Point the cache at ``cache_dir`` and prepare the logger."""
        self._cache_dir = cache_dir
        self._logger = get_logger("embedding_cache")

    @property
    def cache_dir(self) -> Path:
        """Root directory holding the cached vectors."""
        return self._cache_dir

    def key(self, content_hash: str, model_name: str, model_version: str) -> str:
        """Derive the cache key for a content hash under a model namespace.

        The returned relative path encodes all three cache-key components
        (SPEC §13) and is safe to join under the cache directory.
        """
        return f"{model_name}/{model_version}/{content_hash}.npy"

    def get(self, key: str) -> np.ndarray | None:
        """Return the stored vector for ``key`` or None on a miss.

        A corrupt cache entry is deleted and reported as a miss so a bad file
        never poisons a run; the vector is simply recomputed deterministically.
        """
        path = self._cache_dir / key
        if not path.is_file():
            return None
        try:
            return np.asarray(np.load(path))
        except (OSError, ValueError) as exc:
            self._logger.warning(
                "cache_entry_corrupt",
                key=key,
                cause=str(exc),
            )
            path.unlink(missing_ok=True)
            return None

    def put(self, key: str, vector: np.ndarray) -> None:
        """Persist ``vector`` under ``key`` using an atomic replace."""
        path = self._cache_dir / key
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = path.with_name(f"{path.stem}.tmp.npy")
        np.save(temporary_path, vector)
        temporary_path.replace(path)

    def contains(self, key: str) -> bool:
        """Whether ``key`` currently exists on disk (used by ``detect``)."""
        return (self._cache_dir / key).is_file()
