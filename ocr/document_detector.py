# -*- coding: utf-8 -*-

"""Document image detector.

Detects the paper area before OCR processing.
Designed for photographed engineering reports.

The first version keeps OpenCV optional to maintain Win7 compatibility.
"""

from pathlib import Path


class DocumentDetector:

    def __init__(self):
        self.available = False

        try:
            import cv2
            self.cv2 = cv2
            self.available = True
        except ImportError:
            self.cv2 = None

    def detect_and_crop(self, image_path, output_path):
        """Detect document area and save cropped image.

        If OpenCV is unavailable or detection fails,
        returns original image copy path.
        """

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

        cropped = self._find_document(image)

        if cropped is None:
            self.cv2.imwrite(
                str(output_path),
                image
            )
            return str(output_path)

        self.cv2.imwrite(
            str(output_path),
            cropped
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
            area = cv2.contourArea(contour)

            if area < image.shape[0] * image.shape[1] * 0.2:
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
                return self._perspective_transform(
                    image,
                    approx
                )

        return None

    def _perspective_transform(self, image, points):
        """Placeholder for four-point transform.

        Kept isolated for later refinement.
        """

        cv2 = self.cv2
        rect = points.reshape(4, 2)

        x, y, w, h = cv2.boundingRect(points)

        return image[
            y:y+h,
            x:x+w
        ]

    def _copy_original(self, source, target):
        import shutil

        shutil.copy2(
            source,
            target
        )

        return str(target)
