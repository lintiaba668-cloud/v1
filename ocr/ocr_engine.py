"""
OCR识别引擎接口
"""

from .text_parser import parse_report_text


class OCREngine:
    def __init__(self):
        self.enabled = False

    def recognize(self, image_path):
        """
        OCR入口。
        当前版本保留接口，下一步接入PaddleOCR。
        """
        return {
            'image': str(image_path),
            'project_name': '',
            'project_code': ''
        }

    def parse_text(self, text):
        return parse_report_text(text)
