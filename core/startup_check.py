"""
启动环境检查模块
绿色版运行检测
兼容源码运行和PyInstaller EXE运行
"""

from core.resource import get_resource_path
from core.error_code import ErrorCode
from core.logger import get_logger


logger = get_logger("Startup")


class StartupCheck:
    """PowerRename启动前环境检查"""

    def __init__(self):
        self.errors = []

    def add_error(self, code, message, detail=""):
        error = {
            "code": code,
            "message": message,
            "detail": detail
        }

        self.errors.append(error)

        logger.error(
            "[%s] %s | %s",
            code,
            message,
            detail
        )

    def check_ocr(self):
        """检查内置Tesseract及语言包"""

        ocr_exe = get_resource_path(
            'engine/tesseract.exe'
        )

        tessdata = get_resource_path(
            'engine/tessdata'
        )

        if not ocr_exe.exists():
            self.add_error(
                ErrorCode.ENGINE_MISSING,
                "OCR engine missing",
                str(ocr_exe)
            )

        if not tessdata.exists():
            self.add_error(
                ErrorCode.LANGUAGE_DATA_MISSING,
                "OCR language directory missing",
                str(tessdata)
            )
            return

        required = [
            'chi_sim.traineddata',
            'eng.traineddata'
        ]

        for filename in required:
            path = tessdata / filename

            if not path.exists():
                self.add_error(
                    ErrorCode.LANGUAGE_DATA_MISSING,
                    "OCR language data missing",
                    filename
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

                    logger.info(
                        "Created directory: %s",
                        folder
                    )

                except Exception as e:
                    self.add_error(
                        ErrorCode.OUTPUT_FAILED,
                        "Cannot create directory",
                        str(e)
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

            if test_file.exists():
                test_file.unlink()

        except Exception as e:
            self.add_error(
                ErrorCode.OUTPUT_FAILED,
                "No write permission",
                str(e)
            )

    def run(self):
        self.errors = []

        logger.info("Startup check begin")

        try:
            self.check_ocr()
            self.check_directory()
            self.check_write_permission()

        except Exception as e:
            self.add_error(
                ErrorCode.CONFIG_ERROR,
                "Startup check exception",
                str(e)
            )

        success = len(self.errors) == 0

        if success:
            logger.info("Startup check passed")
        else:
            logger.error(
                "Startup check failed: %s errors",
                len(self.errors)
            )

        return {
            'ok': success,
            'errors': self.errors
        }
