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

    def process(self, _image, recognition_mode='deep'):
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


class RankedProjectService:

    def match_project(self, project_name='', project_code=''):
        if project_code:
            return {
                'status': 'matched',
                'auto_accepted': True,
                'match_source': 'project_code_sequence',
                'reason': 'sequence_suffix_equivalent',
                'score': 99.0,
                'margin': 100.0,
                'project_code': '18132026000102',
                'project_name': '编号等价工程',
                'candidates': [],
            }

        return {
            'status': 'matched',
            'auto_accepted': True,
            'match_source': 'project_name',
            'reason': 'score_and_margin_passed',
            'score': 100.0,
            'margin': 100.0,
            'project_code': 'WRONG',
            'project_name': '名称误导工程',
            'candidates': [],
        }


class FilenameHintProjectService:
    def __init__(self):
        self.project = {
            'project_code': 'C5132026Z015',
            'project_name': '莆田荔城某迁改工程',
        }

    def find_by_code(self, code):
        if code == self.project['project_code']:
            return dict(self.project)
        return None

    def match_project(self, project_name='', project_code=''):
        return {
            'status': 'unmatched',
            'auto_accepted': False,
            'match_source': 'none',
            'reason': 'empty_ocr_candidates',
            'score': 0.0,
            'margin': 0.0,
            'project_code': '',
            'project_name': '',
            'candidates': [],
        }


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


def test_sequence_code_attempt_outranks_higher_name_score(tmp_path):
    service = OCRRenameService(
        tmp_path / 'output',
        project_service=RankedProjectService(),
    )

    result = service._match_candidates(
        name_candidates=['名称误导工程'],
        code_candidates=['181320260001-1'],
    )

    assert result['match_source'] == 'project_code_sequence'
    assert result['project_code'] == '18132026000102'


def test_conflicting_exact_code_candidates_require_review(tmp_path):
    class ConflictingCodeService:
        def match_project(self, project_name='', project_code=''):
            if project_code:
                return {
                    'status': 'matched',
                    'auto_accepted': True,
                    'match_source': 'project_code',
                    'reason': 'exact_project_code',
                    'score': 100.0,
                    'margin': 100.0,
                    'project_code': project_code,
                    'project_name': '工程' + project_code,
                    'candidates': [],
                }
            return {
                'status': 'unmatched',
                'auto_accepted': False,
                'match_source': 'none',
                'reason': 'empty_ocr_project_name',
                'score': 0.0,
                'margin': 0.0,
                'project_code': '',
                'project_name': '',
                'candidates': [],
            }

    service = OCRRenameService(
        tmp_path / 'output',
        project_service=ConflictingCodeService(),
    )

    result = service._match_candidates(
        name_candidates=[],
        code_candidates=['CODE001', 'CODE002'],
    )

    assert result['status'] == 'uncertain'
    assert not result['auto_accepted']
    assert result['reason'] == 'conflicting_code_candidates'


def test_exact_generated_filename_rescues_failed_ocr(tmp_path):
    source = (
        tmp_path
        / '莆田荔城某迁改工程_C5132026Z015_开工.jpg'
    )
    source.write_bytes(b'image')
    service = OCRRenameService(
        tmp_path / 'output',
        project_service=FilenameHintProjectService(),
    )
    service.pipeline = FakePipeline(project_name='', project_code='')

    result = service.process(source)

    assert result['status'] == 'success'
    assert result['match_source'] == 'verified_filename'
    assert result['project_code'] == 'C5132026Z015'
    assert result['filename_tag'] == '开工'


def test_mismatched_filename_name_is_not_trusted(tmp_path):
    source = tmp_path / '错误工程_C5132026Z015_开工.jpg'
    source.write_bytes(b'image')
    service = OCRRenameService(
        tmp_path / 'output',
        project_service=FilenameHintProjectService(),
    )
    service.pipeline = FakePipeline(project_name='', project_code='')

    result = service.process(source)

    assert result['status'] == 'unmatched'
    assert result['match_source'] != 'verified_filename'


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
    assert result['filename_tag'] == ''
    assert source.exists()
    assert (output_dir / '标准工程一_P001.jpg').exists()


def test_start_report_uses_excel_code_and_start_suffix(tmp_path):
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
        'project_code': '1813202400START',
        'project_name': '标准工程一',
        'suggested_project_code': '1813202400START',
        'suggested_project_name': '标准工程一',
        'candidates': [],
    })

    service = OCRRenameService(output_dir, project_service=project_service)
    service.pipeline = FakePipeline('OCR工程', '', 'start')

    result = service.process(source)

    assert result['status'] == 'success'
    assert result['report_type'] == 'start'
    assert result['project_code'] == '1813202400START'
    assert result['filename_project_code'] == '1813202400START'
    assert result['filename_tag'] == '开工'
    assert source.exists()
    assert (
        output_dir / '标准工程一_1813202400START_开工.jpg'
    ).exists()


def test_matched_project_without_code_is_rejected(tmp_path):
    source = tmp_path / 'source.jpg'
    source.write_bytes(b'image')

    project_service = FakeProjectService({
        'status': 'matched',
        'auto_accepted': True,
        'match_source': 'project_name',
        'reason': 'score_and_margin_passed',
        'score': 90.0,
        'margin': 20.0,
        'project_code': '',
        'project_name': '标准工程一',
        'suggested_project_code': '',
        'suggested_project_name': '标准工程一',
        'candidates': [],
    })

    service = OCRRenameService(
        tmp_path / 'output',
        project_service=project_service
    )
    service.pipeline = FakePipeline('OCR工程', '', 'start')

    result = service.process(source)

    assert result['status'] == 'failed'
    assert '缺少工程编号' in result['error']
    assert source.exists()


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
