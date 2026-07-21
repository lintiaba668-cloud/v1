"""
OCR图片预处理模块 V2.4
增加尺寸自适应，避免手机原图过大影响Tesseract布局分析。
"""

import logging
from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageChops

logger = logging.getLogger("PowerRename.OCR")

DEFAULT_REGION = {
    'enabled': False,
    'top_percent': 25
}

MAX_SIDE = 2500
DEBUG_DIR = Path('logs/preprocess')


def preprocess(image_path, output_path, ocr_region=None):
    logger.info('[PREPROCESS] start')

    img = Image.open(image_path)

    logger.info('[IMAGE] width=%s height=%s', img.width, img.height)

    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    img.save(DEBUG_DIR / '01_original.jpg')

    img = ImageOps.exif_transpose(img)
    img.save(DEBUG_DIR / '02_rotate.jpg')

    region = ocr_region or DEFAULT_REGION

    if region.get('enabled', False):
        percent = region.get('top_percent', 25)
        img = crop_header_area(img, percent)
        logger.info('[CROP] top_percent=%s', percent)
    else:
        logger.info('[CROP] disabled')

    img.save(DEBUG_DIR / '03_crop.jpg')

    img = resize_for_ocr(img, MAX_SIDE)
    img.save(DEBUG_DIR / '04_resize.jpg')

    img = trim_border(img)

    img = img.convert('L')
    img = ImageEnhance.Contrast(img).enhance(1.3)
    img = img.filter(ImageFilter.SHARPEN)

    img.save(DEBUG_DIR / '05_enhance.jpg')

    logger.info('[PREPROCESS] output width=%s height=%s', img.width, img.height)

    img.save(output_path)
    return output_path


def resize_for_ocr(img, max_side=2500):
    width, height = img.size
    longest = max(width, height)

    if longest <= max_side:
        logger.info('[RESIZE] skip')
        return img

    scale = max_side / longest
    new_size = (
        int(width * scale),
        int(height * scale)
    )

    logger.info('[RESIZE] %s -> %s', img.size, new_size)

    return img.resize(new_size, Image.Resampling.LANCZOS)


def crop_header_area(img, top_percent=25):
    width, height = img.size
    percent = max(5, min(top_percent, 100))
    return img.crop((0, 0, width, int(height * percent / 100)))


def trim_border(img):
    temp = img.convert('RGB')
    bg = Image.new('RGB', temp.size, temp.getpixel((0, 0)))
    diff = ImageChops.difference(temp, bg)
    box = diff.getbbox()

    if box:
        return img.crop(box)

    return img


def crop_header(image_path, output_path):
    img = Image.open(image_path)
    img = crop_header_area(img, 28)
    img.save(output_path)
    return output_path
