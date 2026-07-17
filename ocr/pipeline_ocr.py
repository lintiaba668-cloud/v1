"""
OCR完整处理链
图片 -> OCR文字 -> 工程信息
"""

from .paddle_engine import PaddleEngine
from .parser_v2 import parse_engineering_text
from .confidence import check_result


class OCRPipeline:
    def __init__(self):
        self.engine = PaddleEngine()

    def process(self, image):
        text = self.engine.recognize(image)
        result = parse_engineering_text(text)

        return {
            'text': text,
            'data': result,
            'valid': check_result(result)
        }
