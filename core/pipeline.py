"""
PowerRename处理流水线。
连接：扫描 -> OCR -> 解析 -> 项目明细匹配 -> 命名。
"""

from pathlib import Path

from ocr.ocr_engine import OCREngine
from core.rename import rename_file
from project.project_service import ProjectService


class RenamePipeline:
    def __init__(self, output_dir, project_service=None):
        self.output_dir = Path(output_dir)
        self.ocr = OCREngine()
        self.project_service = project_service or ProjectService()

    def process_text_result(self, image_path, text):
        """Backward-compatible entry point.

        Returns the renamed Path only after an automatically accepted project
        match. Review-required and unmatched results return None.
        """

        detail = self.process_text_result_detail(image_path, text)

        if detail.get('status') != 'success':
            return None

        return Path(detail['target'])

    def process_text_result_detail(self, image_path, text):
        """Return an auditable match and rename decision."""

        image_path = Path(image_path)
        result = self.ocr.parse_text(text)

        project_name = result.get('project_name', '')
        project_code = result.get('project_code', '')

        if not project_name:
            return {
                'status': 'failed',
                'source': str(image_path),
                'target': '',
                'error': 'OCR文本未提取到工程名称',
                'ocr_project_name': '',
                'ocr_project_code': project_code,
                'matched': False,
            }

        match = self.project_service.match_project(
            project_name=project_name,
            project_code=project_code
        )

        if not match.get('auto_accepted'):
            match_status = match.get('status', 'unmatched')
            return {
                'status': (
                    'review_required'
                    if match_status == 'uncertain'
                    else 'unmatched'
                ),
                'source': str(image_path),
                'target': '',
                'ocr_project_name': project_name,
                'ocr_project_code': project_code,
                'project_name': '',
                'project_code': '',
                'suggested_project_name': match.get(
                    'suggested_project_name', ''
                ),
                'suggested_project_code': match.get(
                    'suggested_project_code', ''
                ),
                'matched': False,
                'match_source': match.get('match_source', 'none'),
                'match_score': match.get('score', 0.0),
                'match_margin': match.get('margin', 0.0),
                'match_reason': match.get('reason', ''),
                'candidates': match.get('candidates', []),
            }

        standard_name = match.get('project_name', '')
        standard_code = match.get('project_code', '')

        if not standard_name:
            return {
                'status': 'failed',
                'source': str(image_path),
                'target': '',
                'error': '匹配结果缺少标准工程名称',
                'ocr_project_name': project_name,
                'ocr_project_code': project_code,
                'matched': False,
            }

        target = rename_file(
            image_path,
            self.output_dir,
            standard_name,
            standard_code
        )

        return {
            'status': 'success',
            'source': str(image_path),
            'target': str(target),
            'ocr_project_name': project_name,
            'ocr_project_code': project_code,
            'project_name': standard_name,
            'project_code': standard_code,
            'matched': True,
            'match_source': match.get('match_source', ''),
            'match_score': match.get('score', 0.0),
            'match_margin': match.get('margin', 0.0),
            'match_reason': match.get('reason', ''),
            'candidates': match.get('candidates', []),
        }
