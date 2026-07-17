"""
图片扫描模块
"""

from pathlib import Path

IMAGE_EXT = {
    '.jpg', '.jpeg', '.png',
    '.bmp', '.tif', '.tiff'
}


def scan_images(path):
    """扫描图片，返回图片列表"""
    target = Path(path)
    result = []

    if target.is_file():
        if target.suffix.lower() in IMAGE_EXT:
            result.append(target)

    elif target.is_dir():
        for item in target.rglob('*'):
            if item.is_file() and item.suffix.lower() in IMAGE_EXT:
                result.append(item)

    return result
