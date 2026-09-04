"""Output-schema models - the hard PRD/SPEC contract (SPEC §6.1, ED-7).

These Pydantic models validate at the boundary with ``extra="forbid"`` so any
out-of-contract value fails the run instead of being silently emitted
(parse-don't-validate, type-safety skill). They are intentionally separate
from the in-memory entities: raw signals never appear here.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class FlaggedImage(BaseModel):
    """One suspicious image entry in the per-outlet result (SPEC §6.1)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    file_name: str = Field(min_length=1)
    suspicion_score: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)


def _default_flagged_images() -> list[FlaggedImage]:
    """Empty flag-list factory so the default is explicitly typed."""
    return []


class OutletResult(BaseModel):
    """The per-outlet record from the PRD "Expected Output Format" (SPEC §6.1).

    ``total_images`` counts evaluated images (post corrupt-filtering);
    ``flagged_images`` is empty (never omitted) when nothing is flagged;
    ``ranking`` is optional and, when present, is a permutation of the
    outlet's file names ordered most -> least suspicious.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    outlet_id: str = Field(min_length=1)
    total_images: int = Field(ge=0)
    flagged_images: list[FlaggedImage] = Field(default_factory=_default_flagged_images)
    ranking: list[str] | None = None


def build_outlet_result(
    outlet_id: str,
    total_images: int,
    flagged_images: list[FlaggedImage],
    ranking: list[str],
) -> OutletResult:
    """Assemble and validate one OutletResult (Builder pattern, SPEC §19).

    Centralizes assembly so every call site emits a schema-valid record; a
    violation of the contract raises here rather than at write time.
    """
    return OutletResult(
        outlet_id=outlet_id,
        total_images=total_images,
        flagged_images=flagged_images,
        ranking=ranking,
    )
