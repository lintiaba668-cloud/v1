"""
PowerRename V1 程序入口
Win7兼容版
"""

import sys

from PyQt5.QtWidgets import QApplication, QMessageBox

from core.startup_check import StartupCheck
from ui.main_window_v3 import MainWindowV3


if __name__ == '__main__':
    app = QApplication(sys.argv)

    check = StartupCheck()
    result = check.run()

    if not result['ok']:
        QMessageBox.warning(
            None,
            '运行环境检查',
            '\n'.join(result['errors'])
        )

    window = MainWindowV3()
    window.show()

    sys.exit(app.exec_())
