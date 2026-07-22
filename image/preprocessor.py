# -*- coding: utf-8 -*-
"""
Document image preprocessing pipeline.

V3.2 Lite:
- remove background interference
- perspective correction preparation
- OCR region preparation
"""

import cv2
import numpy as np


class DocumentPreprocessor:

    def crop_document(self, image):
        """Detect document area and remove surrounding background."""

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        edge = cv2.Canny(blur, 50, 150)

        contours, _ = cv2.findContours(
            edge,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return image

        contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(contour)

        if area < image.shape[0] * image.shape[1] * 0.2:
            return image

        x, y, w, h = cv2.boundingRect(contour)

        return image[y:y+h, x:x+w]

    def top_region(self, image, ratio=0.25):
        """Extract document header for project information OCR."""

        height = image.shape[0]
        return image[:int(height * ratio), :]

    def enhance(self, image):
        """Improve contrast before OCR."""

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        return cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            10
        )
