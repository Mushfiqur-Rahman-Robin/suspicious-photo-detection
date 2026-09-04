"""Unit tests: exception hierarchy + exit codes (SPEC §7)."""

from __future__ import annotations

from core.exceptions import (
    ConfigurationError,
    CorruptImageError,
    SpdError,
    UsageError,
)


def test_spd_error_default_exit_code_is_one():
    assert SpdError().exit_code == 1


def test_configuration_error_exit_code_is_two():
    assert ConfigurationError.exit_code == 2


def test_usage_error_exit_code_is_two():
    assert UsageError.exit_code == 2


def test_corrupt_image_error_message_is_actionable():
    error = CorruptImageError("outlet_1", "img.jpg", "not a decodable image: boom")
    assert error.outlet_id == "outlet_1"
    assert error.file_name == "img.jpg"
    assert "outlet_1/img.jpg" in str(error)
    assert "boom" in str(error)


def test_all_domain_errors_are_spd_errors():
    for cls in (ConfigurationError, UsageError, CorruptImageError):
        assert issubclass(cls, SpdError)
