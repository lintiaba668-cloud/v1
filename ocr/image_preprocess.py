"""
OCR图片预处理模块 V2.2
增加明确调试日志，确认预处理链路是否真正执行。
"""

import logging
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageChops

logger = logging.getLogger("PowerRename.OCR")

DEFAULT_REGION = {
    'enabled': True,
    'top_percent': 25
}


def preprocess(image_path, output_path, ocr_region=None):
    logger.info('[PREPROCESS] start')

    img = Image.open(image_path)

    logger.info(
        '[IMAGE] width=%s height=%s',
        img.width,
        img.height
    )

    # EXIF方向纠正必须在裁剪前
    before_size = img.size
    img = ImageOps.exif_transpose(img)

    if img.size != before_size:
        logger.info('[ROTATE] EXIF orientation corrected')
    else:
        logger.info('[ROTATE] no EXIF rotation')

    region = ocr_region or DEFAULT_REGION

    if region.get('enabled', False):
        percent = region.get('top_percent', 25)
        img = crop_header_area(img, percent)

        logger.info(
            '[CROP] top_percent=%s crop_height=%s',
            percent,
            img.height
        )
    else:
        logger.info('[CROP] disabled')

    img = trim_border(img)

    img = img.convert('L')
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = img.filter(ImageFilter.SHARPEN)
    img = img.resize((img.width * 2, img.height * 2))

    logger.info(
        '[PREPROCESS] output width=%s height=%s',
        img.width,
        img.height
    )

    img.save(output_path)

    return output_path


def crop_header_area(img, top_percent=25):
    width, height = img.size

    percent = max(
        5,
        min(top_percent, 100)
    )

    return img.crop(
        (0, 0, width, int(height * percent / 100))
    )


def trim_border(img):
    if img.mode != 'RGB':
        temp = img.convert('RGB')
    else:
        temp = img

    bg = Image.new(
        'RGB',
        temp.size,
        temp.getpixel((0, 0))
    )

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
