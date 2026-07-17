"""
OCR图片预处理模块 V1.2
用于提升电力开竣工报告识别效果
"""

from PIL import Image, ImageOps, ImageEnhance


def preprocess(image_path, output_path):
    """扫描件增强处理"""
    img = Image.open(image_path)

    # 自动纠正方向
    img = ImageOps.exif_transpose(img)

    # 灰度化
    img = img.convert('L')

    # 对比度增强
    img = ImageEnhance.Contrast(img).enhance(2.0)

    # 放大提高小字体识别率
    img = img.resize((img.width * 2, img.height * 2))

    img.save(output_path)

    return output_path


def crop_header(image_path, output_path):
    """
    截取竣工验收报告顶部区域
    用于识别工程名称和工程编号
    """
    img = Image.open(image_path)

    width, height = img.size
    header = img.crop((0, 0, width, int(height * 0.28)))
    header.save(output_path)

    return output_path
