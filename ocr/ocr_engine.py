"""
OCR识别引擎接口
优化版：接入图片预处理和OCR结果解析流程
"""

from pathlib import Path

from .text_parser import parse_report_text
from .image_preprocess import preprocess, crop_header


class OCREngine:
    def __init__(self):
        self.enabled = True
        self.last_error = ''

    def recognize(self, image_path):
        """
        OCR入口。
       
        当前先完成流程接通：
        图片预处理 -> OCR调用 -> 文本解析。
        后续可替换具体OCR引擎，不影响上层流程。
        """
        try:
            image_path = Path(image_path)
            temp_path = image_path.with_name(image_path.stem + '_ocr.jpg')

            preprocess(str(image_path), str(temp_path))

            # OCR引擎接口位置
            # 后续接入PaddleOCR/Tesseract时只替换这里
            raw_text = ''

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
