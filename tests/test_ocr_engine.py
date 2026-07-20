# -*- coding: utf-8 -*-

"""OCREngine tests."""

from ocr.ocr_engine import OCREngine
from core.error_code import ErrorCode
from core.ocr_result import OCRResult


def test_ocr_engine_result_contract():
    engine = OCREngine()

    result = OCRResult(
        image="test.jpg",
        status=engine.status,
        error_code=engine.error_code,
        error_message=engine.last_error
    ).to_dict()

    required = {
        "image",
        "raw_text",
        "items",
        "project_name",
        "project_code",
        "status",
        "error_code",
        "error_message",
    }

    assert required.issubset(result.keys())


def test_error_code_default():
    engine = OCREngine()

    assert engine.error_code in [
        ErrorCode.SUCCESS,
        ErrorCode.ENGINE_MISSING
    ]
