"""
OCR识别到自动命名服务
"""

from pathlib import Path

from ocr.pipeline_ocr import OCRPipeline
from core.rename import rename_file
from project.resolver import ProjectResolver


class OCRRenameService:
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.pipeline = OCRPipeline()
        self.project_resolver = ProjectResolver()

    def process(self, image):
        result = self.pipeline.process(image)

        if not result['valid']:
            return {
                'status': 'failed',
                'file': str(image)
            }

        data = result['data']

        resolved = self.project_resolver.resolve(
            data.get('project_name', ''),
            data.get('project_code', '')
        )

        target = rename_file(
            image,
            self.output_dir,
            resolved.project_name,
            resolved.project_code
        )

        return {
            'status': 'success',
            'source': str(image),
            'target': str(target),
            'project_name': resolved.project_name,
            'project_code': resolved.project_code,
            'matched': resolved.matched,
            'match_source': resolved.source
        }
