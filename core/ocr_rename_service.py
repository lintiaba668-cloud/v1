"""
OCR识别到自动命名服务。

只有导入项目明细匹配结果达到自动通过条件时才执行重命名；
候选过近或低置信度结果进入人工复核状态，避免误改文件名。
"""
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
                'matched': False,
            }

        data = result.get('data', {})
        ocr_project_name = data.get('project_name', '')
        ocr_project_code = data.get('project_code', '')

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
                'matched': False,
            }

        return self._rename_with_project(
            image_path=image_path,
            project_name=project_name,
            project_code=project_code,
            original=result,
            match=match,
            manual_confirmed=False
        )

    def confirm_review(self, review_result, selected_project_code):
        """Confirm one review item and rename with an imported project.

        The selected project must exist in the imported project library. This
        prevents free-text edits from bypassing the authoritative project list.
        """
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
        original,
        match,
        manual_confirmed
    ):
        if not project_name:
            return self._review_error(original, '标准工程名称为空')

        target = rename_file(
            image_path,
            self.output_dir,
            project_name,
            project_code
        )

        return {
            'status': 'success',
            'source': str(image_path),
            'target': str(target),
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
            'matched': True,
            'manual_confirmed': bool(manual_confirmed),
            'match_source': match.get('match_source', ''),
            'match_score': match.get('score', 0.0),
            'match_margin': match.get('margin', 0.0),
            'match_reason': match.get('reason', ''),
            'candidates': match.get('candidates', []),
        }

    def _review_error(self, item, message):
        return {
            'status': 'failed',
            'source': item.get('source', ''),
            'target': item.get('target', ''),
            'error': message,
            'ocr_project_name': item.get('ocr_project_name', ''),
            'ocr_project_code': item.get('ocr_project_code', ''),
            'project_name': '',
            'project_code': '',
            'matched': False,
            'manual_confirmed': False,
            'candidates': item.get('candidates', []),
        }
