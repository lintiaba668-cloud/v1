# -*- coding: utf-8 -*-

"""Batch worker error handling tests."""

from rename.batch_worker import BatchWorker
from core.error_code import ErrorCode


class MockOCR:
    def recognize(self, image):
        return {
            "project_name": "测试工程",
            "project_code": "ABC123"
        }


class MockRule:
    def build_filename(self, report_type, project_name, project_code=""):
        return project_name


class MockValidator:
    def validate(self, filename):
        return False, "invalid filename"


def test_missing_input_path(tmp_path):
    worker = BatchWorker(
        MockOCR(),
        MockRule(),
        MockValidator()
    )

    result = worker.process_directory(
        tmp_path / "missing",
        tmp_path / "output",
        "start"
    )

    assert result["errors"][0]["code"] == ErrorCode.INPUT_PATH_MISSING


def test_invalid_filename_error(tmp_path):
    worker = BatchWorker(
        MockOCR(),
        MockRule(),
        MockValidator()
    )

    image = tmp_path / "001.jpg"
    image.write_text("test", encoding="utf-8")

    result = worker.process_directory(
        tmp_path,
        tmp_path / "output",
        "start"
    )

    assert result["failed"] == 1
    assert result["errors"][0]["code"] == ErrorCode.INVALID_FILENAME
