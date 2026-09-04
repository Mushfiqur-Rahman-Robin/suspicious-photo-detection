"""Domain exception hierarchy.

Every failure in the pipeline is wrapped in one of these types so the CLI can
map them to the SPEC §7 exit codes (0 success / 2 usage-config / 1 runtime)
and so callers can decide handle/wrap/propagate without string matching
(error-handling skill).
"""

from __future__ import annotations


class SpdError(Exception):
    """Base class for every domain-specific error.

    ``exit_code`` maps the error to the CLI contract (SPEC §7): 1 = runtime
    failure, 2 = invalid usage or configuration.
    """

    exit_code = 1


class ConfigurationError(SpdError):
    """Invalid or unreadable configuration (bad config file, bad flag value)."""

    exit_code = 2


class UsageError(SpdError):
    """Invalid command usage (bad arguments, missing required inputs)."""

    exit_code = 2


class DatasetError(SpdError):
    """Base class for dataset discovery/loading failures (SPEC §5.1)."""


class CorruptImageError(DatasetError):
    """An image file is unreadable, truncated, or exceeds decode bounds.

    Carries the outlet and file name plus the underlying cause so the error
    message is immediately actionable (SPEC §5.1).
    """

    def __init__(self, outlet_id: str, file_name: str, cause: str) -> None:
        """Record the outlet, file, and cause for an actionable error message."""
        super().__init__(f"corrupt image {outlet_id}/{file_name}: {cause}")
        self.outlet_id = outlet_id
        self.file_name = file_name


class EmbeddingError(SpdError):
    """Embedding extraction failed (backend unavailable, model load error)."""


class DetectionError(SpdError):
    """Outlier detection failed for an outlet."""


class CacheError(SpdError):
    """Embedding cache unusable or required embeddings are not cached."""


class WriteError(SpdError):
    """Writing output artifacts (JSON/CSV/summary/write-up) failed."""
