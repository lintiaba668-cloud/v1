"""
PowerRename V1 主窗口最终连接版
Win7兼容版：PyQt5
"""

from PyQt5.QtWidgets import QMainWindow, QFileDialog

from core.final_runner import FinalRunner
from ui.log_manager import LogManager


class MainWindowV3(QMainWindow):
    def __init__(self):
        super().__init__()
        self.runner = FinalRunner()
        self.logger = LogManager()
        self.setWindowTitle('PowerRename V1')
        self.files = []

    def add_files(self, files):
        self.files = files
        self.logger.add(f'加载 {len(files)} 个文件')

    def start(self):
        result = self.runner.run(self.files)
        self.logger.add('处理完成')
        return result

    def select_output(self):
        return QFileDialog.getExistingDirectory(self, '选择输出目录')
