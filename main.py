"""
PowerRename V1 程序入口
"""

import sys

from PySide6.QtWidgets import QApplication

from ui.main_window_v3 import MainWindowV3


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindowV3()
    window.show()
    sys.exit(app.exec())
