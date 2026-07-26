# -*- coding: utf-8 -*-
"""
Document perspective correction module.

Purpose:
    Correct mobile phone photographed documents before OCR.

Features:
    - Detect document contour
    - Perspective transform
    - Fail safely and keep original image

Compatibility:
    Python 3.8+
"""

import logging

from PIL import Image, ImageOps

logger = logging.getLogger("PowerRename.OCR")


try:
    import cv2
    import numpy as np
    CV_AVAILABLE = True
except Exception:
    CV_AVAILABLE = False


def rectify_document(image):
    """
    Try to rectify a photographed document.

    Args:
        image: PIL Image

    Returns:
        PIL Image
    """

    if not CV_AVAILABLE:
        logger.info('[RECTIFY] opencv unavailable')
        return image

    try:
        result = _rectify(image)

        if result is not None:
            logger.info('[RECTIFY] perspective corrected')
            return result

    except Exception as exc:
        logger.warning('[RECTIFY] failed: %s', exc)

    logger.info('[RECTIFY] original image kept')
    return image


def deskew_document(image, max_angle=5.0, step=0.5, minimum_angle=2.0):
    """Correct small camera rotation using Pillow only.

    The optional OpenCV perspective path is not available in the portable
    Win7 build.  Projection-profile deskewing still levels the form rows,
    which is the important prerequisite for reliable first-row field crops.

    Returns:
        (corrected_image, applied_angle)
    """
    try:
        angle = _estimate_skew_angle(
            image,
            max_angle=max_angle,
            step=step,
        )

        # One-degree corrections often introduce more interpolation blur than
        # they remove on phone photos. Only correct a clearly visible tilt.
        if abs(angle) < max(float(minimum_angle), step * 0.75):
            return image, 0.0

        corrected = image.rotate(
            angle,
            resample=Image.Resampling.BICUBIC,
            expand=True,
            fillcolor='white',
        )
        logger.info('[DESKEW] angle=%.2f', angle)
        return corrected, angle

    except Exception as exc:
        logger.warning('[DESKEW] failed: %s', exc)
        return image, 0.0


def _estimate_skew_angle(image, max_angle=5.0, step=0.5):
    gray = ImageOps.autocontrast(image.convert('L'))
    gray.thumbnail((560, 820), Image.Resampling.LANCZOS)

    # Titles and table rows are concentrated in the top portion.  Ignoring
    # signatures and stamps makes the horizontal projection more stable.
    gray = gray.crop((
        0,
        0,
        gray.width,
        max(1, int(gray.height * 0.42)),
    ))

    count = int(round(float(max_angle) / float(step)))
    candidates = []

    for index in range(-count, count + 1):
        angle = index * float(step)
        candidates.append((_projection_score(gray, angle), angle))

    candidates.sort(reverse=True)
    return float(candidates[0][1]) if candidates else 0.0


def _projection_score(image, angle):
    rotated = image.rotate(
        angle,
        resample=Image.Resampling.BILINEAR,
        expand=False,
        fillcolor=255,
    )
    pixels = rotated.load()
    width, height = rotated.size
    projection = []

    for y in range(height):
        dark = 0
        for x in range(width):
            if pixels[x, y] < 165:
                dark += 1
        projection.append(dark)

    return sum(
        (projection[index] - projection[index - 1]) ** 2
        for index in range(1, len(projection))
    )


def _rectify(image):

    rgb = np.array(image.convert('RGB'))

    gray = cv2.cvtColor(
        rgb,
        cv2.COLOR_RGB2GRAY
    )

    blur = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    edges = cv2.Canny(
        blur,
        50,
        150
    )

    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_LIST,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return None

    contours = sorted(
        contours,
        key=cv2.contourArea,
        reverse=True
    )

    for contour in contours[:10]:

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

            points = approx.reshape(4, 2)

            return _warp(
                rgb,
                points
            )

    return None


def _warp(image, points):

    ordered = _order_points(points)

    (tl, tr, br, bl) = ordered

    width = int(max(
        np.linalg.norm(br - bl),
        np.linalg.norm(tr - tl)
    ))

    height = int(max(
        np.linalg.norm(tr - br),
        np.linalg.norm(tl - bl)
    ))

    target = np.array([
        [0, 0],
        [width - 1, 0],
        [width - 1, height - 1],
        [0, height - 1]
    ], dtype='float32')

    matrix = cv2.getPerspectiveTransform(
        ordered.astype('float32'),
        target
    )

    warped = cv2.warpPerspective(
        image,
        matrix,
        (width, height)
    )

    return Image.fromarray(warped)


def _order_points(points):

    rect = np.zeros((4, 2), dtype='float32')

    s = points.sum(axis=1)
    diff = np.diff(points, axis=1)

    rect[0] = points[np.argmin(s)]
    rect[2] = points[np.argmax(s)]
    rect[1] = points[np.argmin(diff)]
    rect[3] = points[np.argmax(diff)]

    return rect
