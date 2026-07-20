# -*- coding: utf-8 -*-

"""Filename validator tests."""

from rename.validator import FilenameValidator


def test_invalid_character_detection():
    validator = FilenameValidator()

    ok, message = validator.validate(
        "test:name"
    )

    assert ok is False
    assert message != ""


def test_sanitize_filename():
    validator = FilenameValidator()

    result = validator.sanitize(
        "test:name"
    )

    assert result == "test_name"


def test_normal_filename():
    validator = FilenameValidator()

    ok, _ = validator.validate(
        "工程名称_ABC123"
    )

    assert ok is True
