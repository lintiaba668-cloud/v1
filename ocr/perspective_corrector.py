# -*- coding: utf-8 -*-

"""Perspective correction for photographed documents.

Used after document boundary detection and before OCR.
"""


class PerspectiveCorrector:

    def __init__(self):
        try:
            import cv2
            import numpy as np
            self.cv2 = cv2
            self.np = np
            self.enabled = True
        except ImportError:
            self.cv2 = None
            self.np = None
            self.enabled = False

    def correct(self, image, points):
        """Apply four point perspective transform.

        points order can be arbitrary quadrilateral points.
        """

        if not self.enabled:
            return image

        ordered = self._order_points(points)

        width = max(
            int(self._distance(ordered[0], ordered[1])),
            int(self._distance(ordered[2], ordered[3]))
        )

        height = max(
            int(self._distance(ordered[0], ordered[3])),
            int(self._distance(ordered[1], ordered[2]))
        )

        destination = self.np.array([
            [0, 0],
            [width - 1, 0],
            [width - 1, height - 1],
            [0, height - 1]
        ], dtype='float32')

        matrix = self.cv2.getPerspectiveTransform(
            self.np.array(ordered, dtype='float32'),
            destination
        )

        return self.cv2.warpPerspective(
            image,
            matrix,
            (width, height)
        )

    def _order_points(self, points):
        pts = self.np.array(points).reshape(4, 2)

        result = self.np.zeros((4, 2), dtype='float32')

        s = pts.sum(axis=1)
        diff = self.np.diff(pts, axis=1)

        result[0] = pts[self.np.argmin(s)]
        result[2] = pts[self.np.argmax(s)]
        result[1] = pts[self.np.argmin(diff)]
        result[3] = pts[self.np.argmax(diff)]

        return result

    def _distance(self, a, b):
        return self.np.linalg.norm(a - b)
