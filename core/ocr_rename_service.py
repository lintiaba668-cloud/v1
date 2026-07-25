"""OCR recognition to standard project matching and file output service."""

from pathlib import Path

from ocr.pipeline_ocr import OCRPipeline
from core.rename import rename_file
from project.project_service import ProjectService


class OCRRenameService:
    def __init__(self, output_dir, project_service=None):
        self.output_dir = Path(output_dir)
        self.pipeline = OCRPipeline()
        self.project_service = project_service or ProjectService()

    def process(self, image):
        image_path = Path(image)
        result = self.pipeline.process(image_path)

        if not result.get('valid'):
            return {
                'status': 'failed',
                'source': str(image_path),
                'target': '',
                'error': result.get('error', 'OCR结果无有效工程名称'),
                'ocr_project_name': '',
                'ocr_project_code': '',
                'report_type': '',
                'matched': False,
            }

        data = result.get('data', {})
        ocr_project_name = data.get('project_name', '')
        ocr_project_code = data.get('project_code', '')
        report_type = data.get('report_type', '')

        match = self.project_service.match_project(
            project_name=ocr_project_name,
            project_code=ocr_project_code
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
                'ocr_project_name': ocr_project_name,
                'ocr_project_code': ocr_project_code,
                'report_type': report_type,
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

        project_name = match.get('project_name', '')
        project_code = match.get('project_code', '')

        if not project_name:
            return {
                'status': 'failed',
                'source': str(image_path),
                'target': '',
                'error': '匹配结果缺少标准工程名称',
                'ocr_project_name': ocr_project_name,
                'ocr_project_code': ocr_project_code,
                'report_type': report_type,
                'matched': False,
            }

        return self._rename_with_project(
            image_path=image_path,
            project_name=project_name,
            project_code=project_code,
            report_type=report_type,
            original=result,
            match=match,
            manual_confirmed=False
        )

    def confirm_review(self, review_result, selected_project_code):
        item = dict(review_result or {})
        status = item.get('status', '')

        if status not in ('review_required', 'unmatched'):
            return self._review_error(item, '当前结果不允许人工确认')

        if item.get('target'):
            return self._review_error(item, '该文件已经生成目标路径')

        source = Path(item.get('source', ''))
        if not source.is_file():
            return self._review_error(item, '原文件不存在或已被移动')

        code = ''.join(str(selected_project_code or '').split()).upper()
        if not code:
            return self._review_error(item, '未选择工程编号')

        project = self.project_service.find_by_code(code)
        if not project:
            return self._review_error(item, '所选工程不在导入项目明细库中')

        return self._rename_with_project(
            image_path=source,
            project_name=project.get('project_name', ''),
            project_code=project.get('project_code', ''),
            report_type=item.get('report_type', ''),
            original=item,
            match={
                'match_source': 'manual_review',
                'score': item.get('match_score', 0.0),
                'margin': item.get('match_margin', 0.0),
                'reason': 'user_confirmed_imported_project',
                'candidates': item.get('candidates', []),
            },
            manual_confirmed=True
        )

    def _rename_with_project(
        self,
        image_path,
        project_name,
        project_code,
        report_type,
        original,
        match,
        manual_confirmed
    ):
        if not project_name:
            return self._review_error(original, '标准工程名称为空')

        resolved_type = self._resolve_report_type(
            report_type,
            original
        )

        # 开工报告即使从Excel匹配到工程编号，文件名也只使用工程名称。
        filename_code = project_code if resolved_type == 'finish' else ''

        target = rename_file(
            image_path,
            self.output_dir,
            project_name,
            filename_code
        )

        return {
            'status': 'success',
            'source': str(image_path),
            'target': str(target),
            'report_type': resolved_type,
            'ocr_project_name': original.get(
                'ocr_project_name',
                original.get('data', {}).get('project_name', '')
                if isinstance(original.get('data'), dict) else ''
            ),
            'ocr_project_code': original.get(
                'ocr_project_code',
                original.get('data', {}).get('project_code', '')
                if isinstance(original.get('data'), dict) else ''
            ),
            'project_name': project_name,
            'project_code': project_code,
            'filename_project_code': filename_code,
            'matched': True,
            'manual_confirmed': bool(manual_confirmed),
            'match_source': match.get('match_source', ''),
            'match_score': match.get('score', 0.0),
            'match_margin': match.get('margin', 0.0),
            'match_reason': match.get('reason', ''),
            'candidates': match.get('candidates', []),
        }

    def _resolve_report_type(self, report_type, original):
        if report_type in ('start', 'finish'):
            return report_type

        data = original.get('data', {}) if isinstance(original, dict) else {}
        ocr_code = (
            original.get('ocr_project_code', '')
            if isinstance(original, dict) else ''
        ) or (data.get('project_code', '') if isinstance(data, dict) else '')

        return 'finish' if ocr_code else 'start'

    def _review_error(self, item, message):
        return {
            'status': 'failed',
            'source': item.get('source', ''),
            'target': item.get('target', ''),
            'error': message,
            'report_type': item.get('report_type', ''),
            'ocr_project_name': item.get('ocr_project_name', ''),
            'ocr_project_code': item.get('ocr_project_code', ''),
            'project_name': '',
            'project_code': '',
            'matched': False,
            'manual_confirmed': False,
            'candidates': item.get('candidates', []),
        }
