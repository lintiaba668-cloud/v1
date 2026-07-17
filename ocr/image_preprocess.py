"""
OCR图片预处理模块 V2.0
用于提升电力开竣工报告识别效果
保持轻量，兼容Win7环境
"""

from PIL import Image, ImageOps, ImageEnhance, ImageFilter


def preprocess(image_path, output_path):
    """
    图片增强处理。

    处理流程：
    方向修正 -> 去边缘空白 -> 灰度 -> 对比度增强 -> 锐化 -> 放大
    """
    img = Image.open(image_path)

    # 自动纠正手机照片方向
    img = ImageOps.exif_transpose(img)

    # 去除四周无效边缘
    img = trim_border(img)

    # 灰度化
    img = img.convert('L')

    # 提升文字和背景对比
    img = ImageEnhance.Contrast(img).enhance(2.0)

    # 轻度锐化
    img = img.filter(ImageFilter.SHARPEN)

    # 放大小字体
    img = img.resize((img.width * 2, img.height * 2))

    img.save(output_path)

    return output_path


def trim_border(img):
    """自动裁剪外围空白区域，减少桌面背景干扰"""
    if img.mode != 'RGB':
        temp = img.convert('RGB')
    else:
        temp = img

    bg = Image.new('RGB', temp.size, temp.getpixel((0, 0)))

    diff = ImageChops.difference(temp, bg)
    box = diff.getbbox()

    if box:
        return img.crop(box)

    return img


def crop_header(image_path, output_path):
    """
    截取竣工验收报告顶部区域。
    用于识别工程名称和工程编号。
    """
    img = Image.open(image_path)

    width, height = img.size
    header = img.crop((0, 0, width, int(height * 0.28)))
    header.save(output_path)

    return output_path


# 延迟导入，避免影响旧环境启动
from PIL import ImageChops
