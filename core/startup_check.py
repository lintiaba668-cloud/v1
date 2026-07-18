"""
启动环境检查模块
绿色版运行检测
兼容源码运行和PyInstaller EXE运行
"""

import sys
from pathlib import Path


class StartupCheck:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            self.base_dir = Path(sys.executable).resolve().parent
        else:
            self.base_dir = Path(__file__).resolve().parent.parent

        self.errors = []

    def check_ocr(self):
        ocr_exe = self.base_dir / 'engine' / 'tesseract.exe'
        tessdata = self.base_dir / 'engine' / 'tessdata'

        if not ocr_exe.exists():
            self.errors.append('缺少OCR组件:tesseract.exe')

        if not tessdata.exists():
            self.errors.append('缺少OCR语言包目录')

    def check_directory(self):
        for folder in ['output', 'logs', 'config']:
            path = self.base_dir / folder
            if not path.exists():
                try:
                    path.mkdir(parents=True)
                except Exception:
                    self.errors.append(f'无法创建目录:{folder}')

    def check_write_permission(self):
        test_file = self.base_dir / 'logs' / '.write_test'

        try:
            test_file.write_text('ok', encoding='utf-8')
            test_file.unlink()
        except Exception:
            self.errors.append('程序目录无写入权限，请移动到可写目录')

    def run(self):
        self.errors = []
        self.check_ocr()
        self.check_directory()
        self.check_write_permission()

        return {
            'ok': len(self.errors) == 0,
            'errors': self.errors
        }
