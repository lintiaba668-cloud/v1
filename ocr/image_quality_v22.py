"""
V2.2 图片质量优化模块
用于提升扫描件OCR稳定性
"""

from PIL import Image, ImageEnhance, ImageOps


def enhance_for_ocr(image_path, output_path):
    img = Image.open(image_path)

    # 自动方向修正
    img = ImageOps.exif_transpose(img)

    # 灰度
    img = img.convert('L')

    # 对比度增强
    img = ImageEnhance.Contrast(img).enhance(2.2)

    # 锐化
    img = ImageEnhance.Sharpness(img).enhance(1.8)

    # 放大
    img = img.resize((img.width * 2, img.height * 2))

    img.save(output_path)

    return output_path
