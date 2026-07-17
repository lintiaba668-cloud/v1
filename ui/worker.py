"""
后台处理线程
避免界面处理时卡死
"""

from PySide6.QtCore import QThread, Signal


class ProcessWorker(QThread):
    progress = Signal(int)
    message = Signal(str)
    finished = Signal()

    def __init__(self, workflow):
        super().__init__()
        self.workflow = workflow

    def run(self):
        self.message.emit('开始处理任务')

        files = self.workflow.files
        total = len(files)

        for index, file in enumerate(files, 1):
            self.message.emit(f'处理中: {file.name}')
            self.progress.emit(int(index / max(total, 1) * 100))

        self.message.emit('处理完成')
        self.finished.emit()
