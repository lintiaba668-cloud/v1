# -*- coding: utf-8 -*-

"""Batch worker tests."""

from rename.batch_worker import BatchWorker


class MockOCR:

    def recognize(self, image):
        return {
            "project_name": "测试工程",
            "project_code": "ABC123"
        }


class MockRule:

    def build_filename(
        self,
        report_type,
        project_name,
        project_code=""
    ):
        return project_name + "_" + project_code


class MockValidator:

    def validate(self, filename):
        return True, ""


def test_batch_worker_init():
    worker = BatchWorker(
        MockOCR(),
        MockRule(),
        MockValidator()
    )

    assert worker.ocr_engine is not None
