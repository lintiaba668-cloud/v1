# -*- coding: utf-8 -*-
"""
Portable application launcher.

Entry point for PyInstaller packaged executable.
"""

import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from build.path_manager import PathManager
from build.config import APP_NAME


class ApplicationLauncher:

    def __init__(self):
        self.app = QApplication(sys.argv)

    def run(self):
        window = MainWindow()
        window.setWindowTitle(APP_NAME)
        window.show()

        return self.app.exec()


if __name__ == '__main__':
    print(PathManager.root_path())
    launcher = ApplicationLauncher()
    sys.exit(launcher.run())
