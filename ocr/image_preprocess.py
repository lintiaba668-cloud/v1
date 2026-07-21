"""
OCR图片预处理模块 V2.1
用于电力开竣工报告识别。
增加OCR有效区域控制，减少无关字段干扰。
"""

from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageChops


DEFAULT_REGION = {
    'enabled': True,
    'top_percent': 25
}


def preprocess(image_path, output_path, ocr_region=None):
    """
    OCR图片预处理。

    流程：
    方向修正
    -> OCR区域裁剪
    -> 边缘处理
    -> 灰度
    -> 对比增强
    -> 锐化
    -> 放大
    """

    img = Image.open(image_path)

    # 手机照片方向修正必须在裁剪前执行
    img = ImageOps.exif_transpose(img)

    region = ocr_region or DEFAULT_REGION

    if region.get('enabled', False):
        img = crop_header_area(
            img,
            region.get('top_percent', 25)
        )

    img = trim_border(img)

    img = img.convert('L')
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = img.filter(ImageFilter.SHARPEN)
    img = img.resize((img.width * 2, img.height * 2))

    img.save(output_path)

    return output_path


def crop_header_area(img, top_percent=25):
    """Crop top OCR region after rotation correction."""

    width, height = img.size

    percent = max(
        5,
        min(top_percent, 100)
    )

    return img.crop(
        (0, 0, width, int(height * percent / 100))
    )


def trim_border(img):
    """Remove surrounding background area."""

    if img.mode != 'RGB':
        temp = img.convert('RGB')
    else:
        temp = img

    bg = Image.new(
        'RGB',
        temp.size,
        temp.getpixel((0, 0))
    )

    diff = ImageChops.difference(
        temp,
        bg
    )

    box = diff.getbbox()

    if box:
        return img.crop(box)

    return img


def crop_header(image_path, output_path):
    """Compatibility interface."""

    img = Image.open(image_path)
    img = crop_header_area(img, 28)
    img.save(output_path)

    return output_path
