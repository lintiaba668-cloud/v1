# -*- coding: utf-8 -*-
"""OCR rename integration tests for imported project matching."""

from core.ocr_rename_service import OCRRenameService


class FakePipeline:
    def __init__(
        self,
        project_name='OCR工程',
        project_code='',
        report_type='start'
    ):
        self.project_name = project_name
        self.project_code = project_code
        self.report_type = report_type

    def process(self, _image):
        return {
            'valid': True,
            'data': {
                'project_name': self.project_name,
                'project_code': self.project_code,
                'report_type': self.report_type,
            },
            'error': '',
        }


class FakeProjectService:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def match_project(self, project_name='', project_code=''):
        self.calls.append((project_name, project_code))
        return dict(self.result)


def test_uncertain_match_does_not_output_file(tmp_path):
    source = tmp_path / 'source.jpg'
    source.write_bytes(b'image')
    output_dir = tmp_path / 'output'

    project_service = FakeProjectService({
        'status': 'uncertain',
        'auto_accepted': False,
        'match_source': 'project_name',
        'reason': 'candidate_scores_too_close',
        'score': 88.0,
        'margin': 2.0,
        'project_code': '',
        'project_name': '',
        'suggested_project_code': 'P001',
        'suggested_project_name': '标准工程一',
        'candidates': [
            {
                'project_code': 'P001',
                'project_name': '标准工程一',
                'score': 88.0,
            }
        ],
    })

    service = OCRRenameService(output_dir, project_service=project_service)
    service.pipeline = FakePipeline('识别工程')

    result = service.process(source)

    assert result['status'] == 'review_required'
    assert result['target'] == ''
    assert result['suggested_project_code'] == 'P001'
    assert source.exists()
    assert not output_dir.exists()


def test_completion_report_outputs_name_and_code_and_preserves_source(tmp_path):
    source = tmp_path / 'source.jpg'
    source.write_bytes(b'image')
    output_dir = tmp_path / 'output'

    project_service = FakeProjectService({
        'status': 'matched',
        'auto_accepted': True,
        'match_source': 'project_code',
        'reason': 'exact_project_code',
        'score': 100.0,
        'margin': 100.0,
        'project_code': 'P001',
        'project_name': '标准工程一',
        'suggested_project_code': 'P001',
        'suggested_project_name': '标准工程一',
        'candidates': [],
    })

    service = OCRRenameService(output_dir, project_service=project_service)
    service.pipeline = FakePipeline('OCR工程', 'P001', 'finish')

    result = service.process(source)

    assert result['status'] == 'success'
    assert result['project_name'] == '标准工程一'
    assert result['project_code'] == 'P001'
    assert source.exists()
    assert (output_dir / '标准工程一_P001.jpg').exists()


def test_start_report_outputs_name_only_even_when_excel_has_code(tmp_path):
    source = tmp_path / 'source.jpg'
    source.write_bytes(b'image')
    output_dir = tmp_path / 'output'

    project_service = FakeProjectService({
        'status': 'matched',
        'auto_accepted': True,
        'match_source': 'project_name',
        'reason': 'score_and_margin_passed',
        'score': 90.0,
        'margin': 20.0,
        'project_code': 'P001',
        'project_name': '标准工程一',
        'suggested_project_code': 'P001',
        'suggested_project_name': '标准工程一',
        'candidates': [],
    })

    service = OCRRenameService(output_dir, project_service=project_service)
    service.pipeline = FakePipeline('OCR工程', '', 'start')

    result = service.process(source)

    assert result['status'] == 'success'
    assert result['report_type'] == 'start'
    assert result['filename_project_code'] == ''
    assert source.exists()
    assert (output_dir / '标准工程一.jpg').exists()


def test_unmatched_result_keeps_original_file(tmp_path):
    source = tmp_path / 'source.jpg'
    source.write_bytes(b'image')

    project_service = FakeProjectService({
        'status': 'unmatched',
        'auto_accepted': False,
        'match_source': 'project_name',
        'reason': 'score_below_threshold',
        'score': 40.0,
        'margin': 5.0,
        'project_code': '',
        'project_name': '',
        'suggested_project_code': '',
        'suggested_project_name': '',
        'candidates': [],
    })

    service = OCRRenameService(
        tmp_path / 'output',
        project_service=project_service
    )
    service.pipeline = FakePipeline('无法匹配工程')

    result = service.process(source)

    assert result['status'] == 'unmatched'
    assert result['target'] == ''
    assert source.exists()
