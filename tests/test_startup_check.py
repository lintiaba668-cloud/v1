# -*- coding: utf-8 -*-

"""StartupCheck tests."""

from pathlib import Path

from core.startup_check import StartupCheck
from core.error_code import ErrorCode


def test_startup_result_structure():
    result = StartupCheck().run()

    assert "ok" in result
    assert "errors" in result
    assert isinstance(result["errors"], list)



def test_error_structure():
    check = StartupCheck()

    check.add_error(
        ErrorCode.ENGINE_MISSING,
        "OCR engine missing",
        "engine/tesseract.exe"
    )

    assert len(check.errors) == 1

    error = check.errors[0]

    assert error["code"] == ErrorCode.ENGINE_MISSING
    assert "message" in error
    assert "detail" in error
