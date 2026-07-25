# -*- coding: utf-8 -*-
"""Manual match-review service tests."""

from pathlib import Path

from core.ocr_rename_service import OCRRenameService


class FakeProjectService:
    def __init__(self):
        self.projects = {
            'P001': {
                'project_code': 'P001',
                'project_name': '10kV福岭线#01杆迁改工程',
            }
        }

    def find_by_code(self, code):
        return self.projects.get(code)


def build_review_item(source):
    return {
        'status': 'review_required',
        'source': str(source),
        'target': '',
        'report_type': 'finish',
        'ocr_project_name': '10kV湖峰线401杆迁改工程',
        'ocr_project_code': '',
        'match_score': 78.0,
        'match_margin': 3.0,
        'candidates': [
            {
                'project_code': 'P001',
                'project_name': '10kV福岭线#01杆迁改工程',
                'score': 78.0,
            }
        ],
    }


def test_manual_review_outputs_with_imported_standard_project(tmp_path):
    source = tmp_path / 'source.jpg'
    source.write_bytes(b'image')
    output_dir = tmp_path / 'output'

    service = OCRRenameService(
        output_dir=output_dir,
        project_service=FakeProjectService(),
    )

    result = service.confirm_review(
        build_review_item(source),
        ' p001 ',
    )

    assert result['status'] == 'success'
    assert result['manual_confirmed'] is True
    assert result['match_source'] == 'manual_review'
    assert result['project_code'] == 'P001'
    assert result['project_name'] == '10kV福岭线#01杆迁改工程'
    assert source.exists()
    assert Path(result['target']).is_file()
    assert Path(result['target']).name.endswith('_P001.jpg')


def test_manual_review_rejects_project_not_in_imported_library(tmp_path):
    source = tmp_path / 'source.jpg'
    source.write_bytes(b'image')

    service = OCRRenameService(
        output_dir=tmp_path / 'output',
        project_service=FakeProjectService(),
    )

    result = service.confirm_review(
        build_review_item(source),
        'UNKNOWN',
    )

    assert result['status'] == 'failed'
    assert '项目明细库' in result['error']
    assert source.is_file()
    assert not (tmp_path / 'output').exists()


def test_manual_review_rejects_already_processed_result(tmp_path):
    source = tmp_path / 'source.jpg'
    source.write_bytes(b'image')
    item = build_review_item(source)
    item['status'] = 'success'
    item['target'] = str(tmp_path / 'existing.jpg')

    service = OCRRenameService(
        output_dir=tmp_path / 'output',
        project_service=FakeProjectService(),
    )

    result = service.confirm_review(item, 'P001')

    assert result['status'] == 'failed'
    assert source.is_file()
