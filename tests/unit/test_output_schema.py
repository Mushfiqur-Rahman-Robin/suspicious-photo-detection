"""Unit tests: output-schema contract (SPEC §6.1, ED-7, P1.1)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from core.output_schema import (
    FlaggedImage,
    OutletResult,
    build_outlet_result,
)


def _sample_flag(score: float = 0.8) -> FlaggedImage:
    return FlaggedImage(
        file_name="img_04.jpg",
        suspicion_score=score,
        reason="Low similarity to cluster centroid",
    )


def test_flagged_image_rejects_out_of_range_score():
    with pytest.raises(ValidationError):
        FlaggedImage(file_name="a.jpg", suspicion_score=1.5, reason="x")


def test_flagged_image_rejects_negative_score():
    with pytest.raises(ValidationError):
        FlaggedImage(file_name="a.jpg", suspicion_score=-0.1, reason="x")


def test_flagged_image_forbids_extra_fields():
    with pytest.raises(ValidationError):
        FlaggedImage(file_name="a.jpg", suspicion_score=0.5, reason="x", extra="nope")


def test_outlet_result_allows_empty_flagged():
    result = OutletResult(outlet_id="outlet_1", total_images=3)
    assert result.flagged_images == []
    assert result.ranking is None


def test_outlet_result_forbids_extra_fields():
    with pytest.raises(ValidationError):
        OutletResult(outlet_id="o", total_images=1, flagged_images=[], bogus=1)


def test_outlet_result_rejects_negative_total():
    with pytest.raises(ValidationError):
        OutletResult(outlet_id="o", total_images=-1)


def test_build_outlet_result_assembles_validated_record():
    flagged = [_sample_flag()]
    ranking = ["img_04.jpg", "img_01.jpg", "img_02.jpg", "img_03.jpg"]
    result = build_outlet_result(
        outlet_id="outlet_0001",
        total_images=4,
        flagged_images=flagged,
        ranking=ranking,
    )
    assert result.outlet_id == "outlet_0001"
    assert result.total_images == 4
    assert result.flagged_images[0].file_name == "img_04.jpg"
    assert result.ranking == ranking


def test_model_dump_json_shape_matches_spec():
    result = build_outlet_result(
        outlet_id="outlet_0001",
        total_images=1,
        flagged_images=[_sample_flag(0.87)],
        ranking=["img_04.jpg"],
    )
    payload = result.model_dump(mode="json")
    assert set(payload) == {"outlet_id", "total_images", "flagged_images", "ranking"}
    assert set(payload["flagged_images"][0]) == {
        "file_name",
        "suspicion_score",
        "reason",
    }
    assert payload["flagged_images"][0]["suspicion_score"] == 0.87


def test_roundtrip_via_model_validate():
    result = build_outlet_result("o", 2, [_sample_flag()], ["a.jpg", "b.jpg"])
    reloaded = OutletResult.model_validate(result.model_dump(mode="json"))
    assert reloaded == result
