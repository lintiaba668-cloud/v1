# -*- coding: utf-8 -*-

"""OCREngine tests."""

from ocr.ocr_engine import OCREngine
from core.error_code import ErrorCode


def test_ocr_engine_result_contract():
    engine = OCREngine()

    result = {
        "image": "test.jpg",
        "raw_text": "",
        "items": [],
        "project_name": "",
        "project_code": "",
        "status": engine.status,
        "error_code": engine.error_code,
        "error_message": engine.last_error,
    }

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
