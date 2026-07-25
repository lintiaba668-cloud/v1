"""
PowerRename V1 主窗口最终连接版。
Win7兼容版：PyQt5。
GUI层不直接阻塞执行OCR任务；人工复核在批处理完成后执行。
"""

from PyQt5.QtWidgets import QDialog, QMainWindow, QFileDialog
from PyQt5.QtCore import QThread, pyqtSignal

from core.final_runner import FinalRunner
from ui.log_manager import LogManager
from ui.match_review_dialog import MatchReviewDialog


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
        self.results = []
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
        self.results = list(result or [])
        self.logger.add(
            f'处理完成，共 {len(self.results)} 个结果'
        )

        reviewed = self.review_pending_results(self.results)

        if reviewed:
            record_file = self.runner.save_results(self.results)
            self.logger.add(
                '人工复核完成，已更新记录：' + str(record_file)
            )

    def review_pending_results(self, results):
        """Review uncertain/unmatched candidates and replace confirmed rows."""
        reviewed_count = 0
        rename_service = self.runner.processor.service

        for index, item in enumerate(list(results)):
            if item.get('status') not in ('review_required', 'unmatched'):
                continue

            candidates = item.get('candidates') or []
            if not candidates:
                self.logger.add(
                    '待复核结果无候选项目：' + item.get('source', '')
                )
                continue

            dialog = MatchReviewDialog(
                rename_service=rename_service,
                review_item=item,
                parent=self,
            )

            if dialog.exec_() == QDialog.Accepted:
                confirmed = dialog.confirmed_result
                if confirmed:
                    results[index] = confirmed
                    reviewed_count += 1
                    self.logger.add(
                        '人工确认成功：{} -> {}'.format(
                            confirmed.get('source', ''),
                            confirmed.get('target', ''),
                        )
                    )
            else:
                self.logger.add(
                    '暂不处理：' + item.get('source', '')
                )

        return reviewed_count

    def on_failed(self, message):
        self.logger.add(
            '处理失败: ' + message
        )

    def select_output(self):
        return QFileDialog.getExistingDirectory(
            self,
            '选择输出目录'
        )
