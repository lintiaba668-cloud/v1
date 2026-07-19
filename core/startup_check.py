"""
启动环境检查模块
绿色版运行检测
兼容源码运行和PyInstaller EXE运行
"""

from core.resource import get_resource_path


class StartupCheck:
    """PowerRename启动前环境检查"""

    def __init__(self):
        self.errors = []

    def check_ocr(self):
        """检查内置Tesseract及语言包"""

        ocr_exe = get_resource_path(
            'engine/tesseract.exe'
        )

        tessdata = get_resource_path(
            'engine/tessdata'
        )

        if not ocr_exe.exists():
            self.errors.append(
                'OCR组件缺失:tesseract.exe，请重新安装完整版本'
            )

        if not tessdata.exists():
            self.errors.append(
                'OCR语言包目录缺失，请重新安装完整版本'
            )
            return

        required = [
            'chi_sim.traineddata',
            'eng.traineddata'
        ]

        for filename in required:
            path = tessdata / filename

            if not path.exists():
                self.errors.append(
                    f'OCR语言包缺失:{filename}'
                )

    def check_directory(self):
        """检查工作目录"""

        for folder in ['output', 'logs', 'config']:
            path = get_resource_path(folder)

            if not path.exists():
                try:
                    path.mkdir(
                        parents=True,
                        exist_ok=True
                    )
                except Exception:
                    self.errors.append(
                        f'无法创建目录:{folder}'
                    )

    def check_write_permission(self):
        """检查程序目录写权限"""

        test_file = get_resource_path(
            'logs/.write_test'
        )

        try:
            test_file.write_text(
                'ok',
                encoding='utf-8'
            )
            test_file.unlink()

        except Exception:
            self.errors.append(
                '程序目录无写入权限，请移动到可写目录'
            )

    def run(self):
        self.errors = []

        try:
            self.check_ocr()
            self.check_directory()
            self.check_write_permission()

        except Exception as e:
            self.errors.append(
                f'启动检测异常:{str(e)}'
            )

        return {
            'ok': len(self.errors) == 0,
            'errors': self.errors
        }
