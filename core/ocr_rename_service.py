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
            'ocr_project_name': ocr_project_name,
            'ocr_project_code': ocr_project_code,
            'project_name': project_name,
            'project_code': project_code,
            'matched': True,
            'match_source': match.get('match_source', ''),
            'match_score': match.get('score', 0.0),
            'match_margin': match.get('margin', 0.0),
            'match_reason': match.get('reason', ''),
            'candidates': match.get('candidates', []),
        }
