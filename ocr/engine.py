# -*- coding: utf-8 -*-
"""
OCR engine abstraction layer.

Provides a unified interface for OCR backends.
Supports offline deployment and future PaddleOCR integration.
"""


class OCREngine:

    def __init__(self, backend='mock'):
        self.backend = backend
        self._engine = None

        self._load_backend()

    def _load_backend(self):
        if self.backend == 'paddle':
            try:
                from paddleocr import PaddleOCR

                self._engine = PaddleOCR(
                    use_angle_cls=True,
                    lang='ch'
                )

            except ImportError:
                self._engine = None

    def recognize(self, image):
        """
        OCR recognition interface.
        """

        if self.backend == 'paddle' and self._engine:
            result = self._engine.ocr(image)
            return self._parse_paddle_result(result)

        return {
            'text': '',
            'confidence': 0
        }

    def _parse_paddle_result(self, result):
        texts = []
        scores = []

        for page in result or []:
            for item in page or []:
                texts.append(item[1][0])
                scores.append(item[1][1])

        return {
            'text': ''.join(texts),
            'confidence': (
                sum(scores) / len(scores)
                if scores else 0
            )
        }
