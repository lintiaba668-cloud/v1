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


def test_fast_mode_does_not_enter_legacy_fallback(tmp_path):
    class EmptyTemplateRecognizer:
        def recognize(self, image_path, accuracy_mode=True):
            assert not accuracy_mode
            return {
                'report_type': '',
                'project_name_candidates': [],
                'project_code_candidates': [],
            }

    engine = OCREngine.__new__(OCREngine)
    engine.enabled = True
    engine.error_code = ErrorCode.SUCCESS
    engine.last_error = ''
    engine.template_recognizer = EmptyTemplateRecognizer()
    legacy_calls = []
    engine._recognize_legacy = lambda image: legacy_calls.append(image)
    image = tmp_path / 'sample.jpg'
    image.write_bytes(b'image')

    result = engine.recognize(image, recognition_mode='fast')

    assert not legacy_calls
    assert result['error_message'] == '快速识别未取得可靠字段'
