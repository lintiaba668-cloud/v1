# -*- coding: utf-8 -*-
"""
OCR processing pipeline.

Unified entry point for image recognition workflow.
"""


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
        self.ocr_engine = ocr_engine

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

        if self.ocr_engine and regions:
            name_text = self.ocr_engine.recognize(
                regions.get('name')
            )

            code_text = self.ocr_engine.recognize(
                regions.get('code')
            )

            if self.correction:
                name_text = self.correction.correct(name_text)

            result['project_name'] = name_text
            result['project_code'] = code_text
            result['confidence'] = 1

        return result
