"""Unit tests: one-page write-up (SPEC §16, FR9, P4.5)."""

from __future__ import annotations

import pytest

from config.settings import Settings
from core.exceptions import WriteError
from core.output_schema import build_outlet_result
from reporting.summary import build_run_summary
from reporting.write_up import compose_write_up, write_write_up


def _summary():
    settings = Settings()
    results = [
        build_outlet_result(
            "outlet_a",
            4,
            [],
            ["a1.jpg", "a2.jpg", "a3.jpg", "a4.jpg"],
        )
    ]
    return build_run_summary("run-1", settings, results, {"embed": 2.0}, 0, 4)


def test_write_up_covers_required_sections():
    write_up = compose_write_up(_summary(), max_chars=10000)
    for section in (
        "## Method",
        "## Measured run",
        "## Validation",
        "## Rationale",
        "## Scalability",
        "## Limitations",
    ):
        assert section in write_up


def test_write_up_documents_qualitative_review():
    write_up = compose_write_up(_summary(), max_chars=10000)
    assert "Qualitative review of real flags" in write_up
    assert "borrowed-photo" in write_up


def test_write_up_is_grounded_in_measured_numbers():
    write_up = compose_write_up(_summary(), max_chars=10000)
    assert "Outlets: 1" in write_up
    assert "images: 4" in write_up
    assert "2.0 images/sec" in write_up


def test_write_up_respects_max_chars():
    write_up = compose_write_up(_summary(), max_chars=200)
    assert len(write_up) <= 200


def test_write_write_up_persists_file(output_dir):
    path = write_write_up(compose_write_up(_summary(), max_chars=10000), output_dir)
    assert path.name == "write_up.md"
    assert path.read_text(encoding="utf-8").startswith("# Suspicious Photo Detection")


def test_write_write_up_error_when_output_is_a_file(tmp_path):
    target = tmp_path / "blocked"
    target.write_text("i am a file")
    with pytest.raises(WriteError):
        write_write_up("content", target)
