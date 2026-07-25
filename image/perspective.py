# -*- coding: utf-8 -*-
"""
Perspective correction for photographed documents.
"""

import cv2
import numpy as np


class PerspectiveCorrector:

    def correct(self, image):
        """Detect document rectangle and perform perspective transform."""

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edge = cv2.Canny(blur, 50, 150)

        contours, _ = cv2.findContours(
            edge,
            cv2.RETR_LIST,
            cv2.CHAIN_APPROX_SIMPLE
        )

        contours = sorted(
            contours,
            key=cv2.contourArea,
            reverse=True
        )

        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(
                contour,
                0.02 * perimeter,
                True
            )

            if len(approx) == 4:
                points = approx.reshape(4, 2)
                return self._warp(image, points)

        return image

    def _warp(self, image, points):
        rect = self._order_points(points)

        width = 1200
        height = 1700

        target = np.array([
            [0, 0],
            [width - 1, 0],
            [width - 1, height - 1],
            [0, height - 1]
        ], dtype='float32')

        matrix = cv2.getPerspectiveTransform(
            rect,
            target
        )

        return cv2.warpPerspective(
            image,
            matrix,
            (width, height)
        )

    def _order_points(self, points):
        rect = np.zeros((4, 2), dtype='float32')

        total = points.sum(axis=1)
        diff = np.diff(points, axis=1)

        rect[0] = points[np.argmin(total)]
        rect[2] = points[np.argmax(total)]
        rect[1] = points[np.argmin(diff)]
        rect[3] = points[np.argmax(diff)]

        return rect
