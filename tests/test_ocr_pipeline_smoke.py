# -*- coding: utf-8 -*-
"""OCR pipeline smoke tests."""

from ocr.pipeline import OCRPipeline


class MockOCR:

    def recognize(self, image):
        return '测试工程' if image == 'name' else 'TEST001'


class MockHeader:

    def split_regions(self, image):
        return {
            'name': 'name',
            'code': 'code'
        }


def test_pipeline_output_contract():
    pipeline = OCRPipeline(
        header_detector=MockHeader(),
        ocr_engine=MockOCR()
    )

    result = pipeline.process('image')

    assert result['project_name'] == '测试工程'
    assert result['project_code'] == 'TEST001'
    assert 'confidence' in result
