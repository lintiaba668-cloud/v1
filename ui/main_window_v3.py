"""
PowerRename V1 主窗口最终连接版
Win7兼容版：PyQt5
GUI层不直接阻塞执行任务。
"""

from PyQt5.QtWidgets import QMainWindow, QFileDialog
from PyQt5.QtCore import QThread, pyqtSignal

from core.final_runner import FinalRunner
from ui.log_manager import LogManager


class RunnerThread(QThread):

    finished = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, runner, files):
        super().__init__()
        self.runner = runner
        self.files = files

    def run(self):
        try:
            self.finished.emit(
                self.runner.run(self.files)
            )
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindowV3(QMainWindow):

    def __init__(self):
        super().__init__()
        self.runner = FinalRunner()
        self.logger = LogManager()
        self.thread = None
        self.setWindowTitle('PowerRename V1')
        self.files = []

    def add_files(self, files):
        self.files = files
        self.logger.add(f'加载 {len(files)} 个文件')

    def start(self):
        if not self.files:
            self.logger.add('没有待处理文件')
            return

        self.thread = RunnerThread(
            self.runner,
            self.files
        )

        self.thread.finished.connect(
            self.on_finished
        )
        self.thread.failed.connect(
            self.on_failed
        )

        self.thread.start()

    def on_finished(self, result):
        self.logger.add(
            f'处理完成，共 {len(result)} 个结果'
        )

    def on_failed(self, message):
        self.logger.add(
            '处理失败: ' + message
        )

    def select_output(self):
        return QFileDialog.getExistingDirectory(
            self,
            '选择输出目录'
        )
