"""
PowerRename V1 程序入口
Win7兼容绿色版
生产启动流程
"""

import sys
import traceback

from PyQt5.QtWidgets import QApplication, QMessageBox

from core.startup_check import StartupCheck
from ui.main_window_v3 import MainWindowV3


def show_error(title, message):
    """统一异常提示，避免EXE环境出现traceback"""

    QMessageBox.critical(
        None,
        title,
        message
    )


def startup():
    """应用启动入口"""

    app = QApplication(sys.argv)

    try:
        check = StartupCheck()
        result = check.run()

        if not result['ok']:
            show_error(
                '运行环境检查失败',
                '\n'.join(result['errors'])
            )
            return 1

        window = MainWindowV3()
        window.show()

        return app.exec_()

    except Exception:
        error = traceback.format_exc()

        show_error(
            '程序启动异常',
            '程序启动失败，请查看logs目录。\n\n' + error
        )

        return 1


if __name__ == '__main__':
    sys.exit(startup())
