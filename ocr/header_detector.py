# -*- coding: utf-8 -*-
"""
Header region detector for engineering document OCR.

Fixed-layout optimization:
- left top region: project name
- right top region: project code
"""


class HeaderDetector:

    def __init__(self, name_ratio=0.5, height_ratio=0.25):
        self.name_ratio = name_ratio
        self.height_ratio = height_ratio

    def split_regions(self, image):
        """Split document header into name and code OCR regions."""

        height, width = image.shape[:2]
        header_height = int(height * self.height_ratio)
        middle = int(width * self.name_ratio)

        return {
            'project_name': image[:header_height, :middle],
            'project_code': image[:header_height, middle:]
        }

    def prepare_ocr(self, image, ocr_engine):
        """Run OCR separately on fixed header regions."""

        regions = self.split_regions(image)

        return {
            'project_name': ocr_engine.recognize(
                regions['project_name']
            ),
            'project_code': ocr_engine.recognize(
                regions['project_code']
            )
        }
