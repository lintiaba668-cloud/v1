"""
PowerRename V1 主窗口整合版
"""

from PySide6.QtWidgets import QMainWindow, QFileDialog

from .app_service import AppService
from .log_manager import LogManager


class MainWindowFinal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.service = AppService()
        self.logger = LogManager()
        self.setWindowTitle('PowerRename V1')

    def load_file(self, path):
        result = self.service.load(path)
        self.logger.add(result['message'])
        return result

    def choose_output(self):
        folder = QFileDialog.getExistingDirectory(self, '选择输出目录')
        return folder
