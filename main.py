"""
PowerRename V1
电力工程开竣工报告批量重命名工具
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow

SUPPORTED_EXT = {
    '.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'
}


def scan_files(folder):
    """扫描图片文件"""
    files = []
    for p in Path(folder).rglob('*'):
        if p.suffix.lower() in SUPPORTED_EXT:
            files.append(p)
    return files


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
