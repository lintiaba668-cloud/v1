"""
OCR识别引擎接口
优化版：接入图片预处理和本地OCR调用
"""

from pathlib import Path

from .text_parser import parse_report_text
from .image_preprocess import preprocess


class OCREngine:
    def __init__(self):
        self.enabled = True
        self.last_error = ''

    def _run_ocr(self, image_path):
        """调用本地OCR，失败时返回空文本。"""
        try:
            import pytesseract
            from PIL import Image

            text = pytesseract.image_to_string(
                Image.open(image_path),
                lang='chi_sim+eng'
            )
            return text
        except Exception as e:
            self.last_error = str(e)
            return ''

    def recognize(self, image_path):
        """
        图片预处理 -> OCR -> 字段解析
        """
        image_path = Path(image_path)
        temp_path = image_path.with_name(image_path.stem + '_ocr.jpg')

        try:
            preprocess(str(image_path), str(temp_path))

            raw_text = self._run_ocr(str(temp_path))
            result = parse_report_text(raw_text)

            return {
                'image': str(image_path),
                'raw_text': raw_text,
                'project_name': result.get('project_name', ''),
                'project_code': result.get('project_code', '')
            }

        except Exception as e:
            self.last_error = str(e)
            return {
                'image': str(image_path),
                'raw_text': '',
                'project_name': '',
                'project_code': ''
            }

    def parse_text(self, text):
        return parse_report_text(text)
