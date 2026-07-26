# -*- coding: utf-8 -*-

from ocr.pipeline_ocr import OCRPipeline


class FakeEngine:

    def __init__(self, result):
        self.result = result

    def recognize(self, _image, recognition_mode='deep'):
        return self.result


def test_start_report_drops_body_number_false_positive():
    pipeline = OCRPipeline.__new__(OCRPipeline)
    pipeline.engine = FakeEngine({
        'report_type': 'start',
        'project_name': '莆田某10kV线路工程',
        'project_name_candidates': ['莆田某10kV线路工程'],
        'project_code': '',
        'project_code_candidates': [],
        'raw_text': '工程编号 0A11HAZE3229',
        'items': [],
        'recognition_source': 'template_fields',
        'error_message': '',
    })

    result = pipeline.process('unused.jpg')

    assert result['valid'] is True
    assert result['data']['project_code'] == ''
    assert result['data']['project_code_candidates'] == []


def test_implausible_legacy_code_is_rejected():
    pipeline = OCRPipeline.__new__(OCRPipeline)
    pipeline.engine = FakeEngine({
        'report_type': '',
        'project_name': '',
        'project_name_candidates': [],
        'project_code': 'TELSHES6591401',
        'project_code_candidates': ['TELSHES6591401'],
        'raw_text': '',
        'items': [],
        'recognition_source': 'legacy_region',
        'error_message': '',
    })

    result = pipeline.process('unused.jpg')

    assert result['valid'] is False
    assert result['data']['project_code'] == ''
