# -*- coding: utf-8 -*-

"""Image orientation detector.

Detects rotated document images before OCR.
Uses Tesseract OSD when available and keeps fallback hooks
for coordinate based orientation analysis.
"""

import re
import subprocess


class OrientationDetector:

    def __init__(self, tesseract_path=None):
        self.tesseract_path = tesseract_path

    def detect(self, image_path):
        """Return rotation angle required to correct image.

        Returns:
            0, 90, 180, 270
        """

        result = self._detect_by_osd(image_path)

        if result is not None:
            return result

        return 0

    def _detect_by_osd(self, image_path):
        if not self.tesseract_path:
            return None

        try:
            process = subprocess.run(
                [
                    str(self.tesseract_path),
                    str(image_path),
                    'stdout',
                    '--psm',
                    '0'
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=15
            )

            output = process.stdout.decode(
                'utf-8',
                errors='ignore'
            )

            match = re.search(
                r'Rotate:\s+(\d+)',
                output
            )

            if not match:
                return None

            rotate = int(match.group(1))

            if rotate in (0, 90, 180, 270):
                return rotate

        except Exception:
            return None

        return None

    def rotate_image(self, image, angle):
        """Rotate OpenCV image."""

        if angle == 90:
            import cv2
            return cv2.rotate(
                image,
                cv2.ROTATE_90_CLOCKWISE
            )

        if angle == 180:
            import cv2
            return cv2.rotate(
                image,
                cv2.ROTATE_180
            )

        if angle == 270:
            import cv2
            return cv2.rotate(
                image,
                cv2.ROTATE_90_COUNTERCLOCKWISE
            )

        return image
