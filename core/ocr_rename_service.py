"""
OCR识别到自动命名服务
"""

from pathlib import Path

from ocr.pipeline_ocr import OCRPipeline
from core.rename import rename_file


class OCRRenameService:
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.pipeline = OCRPipeline()

    def process(self, image):
        result = self.pipeline.process(image)

        if not result['valid']:
            return {
                'status': 'failed',
                'file': str(image)
            }

        data = result['data']

        target = rename_file(
            image,
            self.output_dir,
            data['project_name'],
            data['project_code']
        )

        return {
            'status': 'success',
            'source': str(image),
            'target': str(target),
            'project_name': data['project_name'],
            'project_code': data['project_code']
        }
