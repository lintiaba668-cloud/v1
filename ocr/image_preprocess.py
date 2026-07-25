"""
OCR图片预处理模块 V3.3。
针对手机拍摄报告，裁切顶部字段区域后放大，提升中文小字识别率。
"""

import logging
from pathlib import Path

from PIL import Image, ImageOps, ImageChops

from .document_rectifier import rectify_document

logger = logging.getLogger("PowerRename.OCR")

DEFAULT_REGION = {
    'enabled': False,
    'top_percent': 28
}

MAX_SIDE = 3600
PREFERRED_SCALE = 2.0
DEBUG_DIR = Path('logs/preprocess')


def preprocess(image_path, output_path, ocr_region=None):
    logger.info('[PREPROCESS] start')

    img = Image.open(image_path)
    logger.info('[IMAGE] width=%s height=%s', img.width, img.height)

    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    img.save(DEBUG_DIR / '01_original.jpg')

    img = ImageOps.exif_transpose(img)
    img.save(DEBUG_DIR / '02_rotate.jpg')

    img = rectify_document(img)
    img.save(DEBUG_DIR / '03_rectify.jpg')

    region = ocr_region or DEFAULT_REGION

    if region.get('enabled', False):
        percent = region.get('top_percent', 28)
        img = crop_header_area(img, percent)
        logger.info('[CROP] top_percent=%s', percent)
    else:
        logger.info('[CROP] disabled')

    img.save(DEBUG_DIR / '04_crop.jpg')

    img = trim_border(img)
    img = img.convert('L')
    img = ImageOps.autocontrast(img)
    img = resize_for_ocr(img, MAX_SIDE)

    img.save(DEBUG_DIR / '05_resize.jpg')
    img.save(DEBUG_DIR / '06_enhance.jpg')

    logger.info('[PREPROCESS] output width=%s height=%s', img.width, img.height)

    img.save(output_path)
    return output_path


def resize_for_ocr(img, max_side=MAX_SIDE, preferred_scale=PREFERRED_SCALE):
    width, height = img.size
    longest = max(width, height)

    if longest <= 0:
        return img

    scale = float(preferred_scale)

    if longest * scale > max_side:
        scale = float(max_side) / float(longest)

    if abs(scale - 1.0) < 0.01:
        logger.info('[RESIZE] skip')
        return img

    new_size = (
        max(1, int(round(width * scale))),
        max(1, int(round(height * scale)))
    )

    logger.info('[RESIZE] %s -> %s scale=%.2f', img.size, new_size, scale)
    return img.resize(new_size, Image.Resampling.LANCZOS)


def crop_header_area(img, top_percent=28):
    width, height = img.size
    percent = max(10, min(int(top_percent), 100))
    return img.crop((0, 0, width, int(height * percent / 100.0)))


def trim_border(img):
    temp = img.convert('RGB')
    bg = Image.new('RGB', temp.size, temp.getpixel((0, 0)))
    diff = ImageChops.difference(temp, bg)
    box = diff.getbbox()

    if not box:
        return img

    left, top, right, bottom = box
    width, height = img.size

    if right - left < width * 0.55 or bottom - top < height * 0.35:
        logger.info('[TRIM] suspicious box ignored: %s', box)
        return img

    return img.crop(box)


def crop_header(image_path, output_path):
    img = Image.open(image_path)
    img = crop_header_area(img, 28)
    img.save(output_path)
    return output_path
