"""
输入文件处理模块
支持 ZIP / 图片 / 文件夹
"""

from pathlib import Path
from .scanner import scan_images
from .unzip import extract_zip
from .temp import create_temp_dir


class FileInput:
    def __init__(self):
        self.files = []

    def load(self, path):
        path = Path(path)

        if path.is_dir():
            self.files.extend(scan_images(path))

        elif path.suffix.lower() == '.zip':
            temp = create_temp_dir()
            extract_zip(path, temp)
            self.files.extend(scan_images(temp))

        elif path.suffix.lower() in {
            '.jpg','.jpeg','.png','.bmp','.tif','.tiff'
        }:
            self.files.append(path)

        return self.files
