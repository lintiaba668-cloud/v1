# -*- coding: utf-8 -*-

"""OCRExecutor tests.

These tests validate the execution layer contract.
"""

from pathlib import Path

from ocr.ocr_executor import OCRExecutor
from core.error_code import ErrorCode


def test_execute_result_structure():
    executor = OCRExecutor()

    result = executor._failed(
        ErrorCode.OCR_EXEC_FAILED,
        "mock error"
    )

    assert "success" in result
    assert "error_code" in result
    assert "error_message" in result
    assert result["error_code"] == ErrorCode.OCR_EXEC_FAILED


def test_cleanup_temp_file(tmp_path):
    executor = OCRExecutor()

    temp = tmp_path / "test.tsv"
    temp.write_text("test", encoding="utf-8")

    executor._remove_temp(str(temp))

    assert not temp.exists()
