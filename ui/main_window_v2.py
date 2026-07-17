"""
PowerRename V1 主窗口第二版逻辑
"""

from PySide6.QtWidgets import QMainWindow

from .controller import AppController


class MainWindowV2(QMainWindow):
    def __init__(self):
        super().__init__()
        self.controller = AppController()
        self.setWindowTitle('PowerRename V1')

    def add_file(self, path):
        return self.controller.load_file(path)

    def process(self):
        return self.controller.start()
