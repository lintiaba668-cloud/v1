# -*- coding: utf-8 -*-
"""Backward-compatible OCR processing pipeline."""

from .engine import OCREngine


class OCRPipeline:

    def __init__(
        self,
        preprocessor=None,
        perspective=None,
        header_detector=None,
        correction=None,
        ocr_engine=None
    ):
        self.preprocessor = preprocessor
        self.perspective = perspective
        self.header_detector = header_detector
        self.correction = correction
        self.ocr_engine = ocr_engine or OCREngine()

    def process(self, image):
        current = image

        if self.perspective:
            current = self.perspective.correct(current)

        if self.preprocessor:
            current = self.preprocessor.crop_document(current)
            current = self.preprocessor.enhance(current)

        regions = None

        if self.header_detector:
            regions = self.header_detector.split_regions(current)

        result = {
            'project_name': '',
            'project_code': '',
            'confidence': 0
        }

        if regions:
            name_result = self._normalize_result(
                self.ocr_engine.recognize(regions.get('name'))
            )
            code_result = self._normalize_result(
                self.ocr_engine.recognize(regions.get('code'))
            )

            name_text = name_result.get('text', '')
            code_text = code_result.get('text', '')

            if self.correction:
                name_text = self.correction.correct(name_text)
                code_text = self.correction.correct(code_text)

            result['project_name'] = name_text
            result['project_code'] = code_text
            result['confidence'] = min(
                name_result.get('confidence', 0),
                code_result.get('confidence', 0)
            )

        return result

    @staticmethod
    def _normalize_result(value):
        if isinstance(value, dict):
            return value

        if value is None:
            return {'text': '', 'confidence': 0}

        return {
            'text': str(value),
            'confidence': 0,
        }
