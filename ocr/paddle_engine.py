"""
PaddleOCR 引擎封装
"""


class PaddleEngine:
    def __init__(self):
        self.ocr = None

    def load(self):
        """加载OCR模型"""
        try:
            from paddleocr import PaddleOCR
            self.ocr = PaddleOCR(use_angle_cls=True, lang='ch')
            return True
        except Exception:
            return False

    def recognize(self, image_path):
        """识别图片文字"""
        if self.ocr is None:
            if not self.load():
                return ''

        result = self.ocr.ocr(str(image_path), cls=True)

        texts = []
        if result:
            for line in result[0]:
                texts.append(line[1][0])

        return '\n'.join(texts)
