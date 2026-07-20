# -*- coding: utf-8 -*-

"""OCRResult tests."""

from core.ocr_result import OCRResult


def test_ocr_result_to_dict():
    result = OCRResult(
        image="001.jpg",
        raw_text="工程名称",
        project_name="测试工程",
        project_code="ABC123",
        status="FINISHED"
    )

    data = result.to_dict()

    assert data["image"] == "001.jpg"
    assert data["project_name"] == "测试工程"
    assert data["project_code"] == "ABC123"
    assert "error_code" in data
    assert "error_message" in data


def test_ocr_result_default_items():
    result = OCRResult()

    assert isinstance(result.items, list)
    assert result.to_dict()["items"] == []
