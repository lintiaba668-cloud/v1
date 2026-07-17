"""
OCR图片预处理模块
用于提升扫描件识别效果
"""

from PIL import Image, ImageOps, ImageEnhance


def preprocess(image_path, output_path):
    """图片增强处理"""
    img = Image.open(image_path)

    # 自动纠正方向（基础处理）
    img = ImageOps.exif_transpose(img)

    # 灰度增强
    img = img.convert('L')

    # 提升对比度
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)

    img.save(output_path)

    return output_path
