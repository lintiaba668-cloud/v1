"""
PowerRename处理流水线
连接：扫描 -> OCR -> 解析 -> 命名
"""

from pathlib import Path

from ocr.ocr_engine import OCREngine
from core.rename import rename_file


class RenamePipeline:
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.ocr = OCREngine()

    def process_text_result(self, image_path, text):
        result = self.ocr.parse_text(text)

        project_name = result.get('project_name', '')
        project_code = result.get('project_code', '')

        if not project_name:
            return None

        return rename_file(
            image_path,
            self.output_dir,
            project_name,
            project_code
        )
