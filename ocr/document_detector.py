# -*- coding: utf-8 -*-

"""Document image detector.

Detects photographed engineering report pages and applies
perspective correction before OCR.
"""

from pathlib import Path

from .perspective_corrector import PerspectiveCorrector


class DocumentDetector:

    def __init__(self):
        self.available = False
        self.corrector = PerspectiveCorrector()

        try:
            import cv2
            self.cv2 = cv2
            self.available = True
        except ImportError:
            self.cv2 = None

    def detect_and_crop(self, image_path, output_path):
        image_path = Path(image_path)
        output_path = Path(output_path)

        if not self.available:
            return self._copy_original(
                image_path,
                output_path
            )

        image = self.cv2.imread(str(image_path))

        if image is None:
            raise ValueError(
                'image load failed: ' + str(image_path)
            )

        corrected = self._find_document(image)

        if corrected is None:
            self.cv2.imwrite(
                str(output_path),
                image
            )
        else:
            self.cv2.imwrite(
                str(output_path),
                corrected
            )

        return str(output_path)

    def _find_document(self, image):
        cv2 = self.cv2

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )

        blur = cv2.GaussianBlur(
            gray,
            (5, 5),
            0
        )

        edge = cv2.Canny(
            blur,
            50,
            150
        )

        contours, _ = cv2.findContours(
            edge,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        contours = sorted(
            contours,
            key=cv2.contourArea,
            reverse=True
        )

        for contour in contours[:10]:
            if cv2.contourArea(contour) < image.shape[0] * image.shape[1] * 0.2:
                continue

            perimeter = cv2.arcLength(
                contour,
                True
            )

            approx = cv2.approxPolyDP(
                contour,
                0.02 * perimeter,
                True
            )

            if len(approx) == 4:
                return self.corrector.correct(
                    image,
                    approx
                )

        return None

    def _copy_original(self, source, target):
        import shutil

        shutil.copy2(
            source,
            target
        )

        return str(target)
