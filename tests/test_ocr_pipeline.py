# -*- coding: utf-8 -*-

"""OCR pipeline lifecycle tests."""

from core.ocr_result import OCRResult
from core.status import OCRStatus


def test_pipeline_result_flow_contract():
    result = OCRResult(
        image="001.jpg",
        raw_text="工程名称",
        project_name="测试项目",
        project_code="ABC123",
        status=OCRStatus.FINISHED
    )

    data = result.to_dict()

    assert data["status"] == OCRStatus.FINISHED
    assert data["project_name"] == "测试项目"
    assert data["project_code"] == "ABC123"


def test_failed_pipeline_contract():
    result = OCRResult(
        image="001.jpg",
        status=OCRStatus.FAILED,
        error_code=1,
        error_message="ocr failed"
    )

    data = result.to_dict()

    assert data["status"] == OCRStatus.FAILED
    assert data["error_message"] != ""
