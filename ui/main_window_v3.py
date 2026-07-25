# -*- coding: utf-8 -*-
"""PowerRename V1 main window.

PyQt5 / Win7 compatible workflow:
Excel project list -> images/folder/ZIP -> batch OCR -> Excel correction ->
renamed image output -> result workbook -> manual review when required.
"""

import os
from pathlib import Path
import tempfile
import zipfile

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.final_runner import FinalRunner
from ui.import_dialog import ImportDialog
from ui.log_manager import LogManager
from ui.match_review_dialog import MatchReviewDialog


SUPPORTED_IMAGES = {
    '.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'
}


class RunnerThread(QThread):

    completed = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, runner, files):
        super().__init__()
        self.runner = runner
        self.files = list(files)

    def run(self):
        try:
            self.completed.emit(self.runner.run(self.files))
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindowV3(QMainWindow):

    def __init__(self):
        super().__init__()

        self.runner = FinalRunner()
        self.logger = LogManager()
        self.thread = None
        self.results = []
        self.files = []
        self.output_dir = Path('output').resolve()
        self.temp_root = Path('temp/imported').resolve()

        self.setWindowTitle('PowerRename V1 - 开竣工报告批量重命名')
        self.resize(960, 680)
        self.setAcceptDrops(True)
        self._build_ui()
        self._append_log('程序已启动，请先导入工程明细Excel。')

    def _build_ui(self):
        central = QWidget(self)
        layout = QVBoxLayout(central)

        title = QLabel('配网工程开竣工报告批量重命名工具')
        title.setStyleSheet('font-size: 20px; font-weight: bold;')

        rule = QLabel(
            '命名规则：开工报告 = 工程名称_工程编号_开工.jpg；'
            '竣工验收报告 = 工程名称_工程编号.jpg。'
        )
        rule.setWordWrap(True)

        button_row = QHBoxLayout()
        self.import_excel_btn = QPushButton('1. 导入工程明细Excel')
        self.add_images_btn = QPushButton('2. 添加图片')
        self.add_folder_btn = QPushButton('添加文件夹')
        self.clear_btn = QPushButton('清空列表')
        self.output_btn = QPushButton('选择输出目录')
        self.start_btn = QPushButton('3. 开始批量处理')

        button_row.addWidget(self.import_excel_btn)
        button_row.addWidget(self.add_images_btn)
        button_row.addWidget(self.add_folder_btn)
        button_row.addWidget(self.clear_btn)
        button_row.addWidget(self.output_btn)
        button_row.addWidget(self.start_btn)

        self.output_label = QLabel('输出目录：' + str(self.output_dir))
        self.output_label.setWordWrap(True)

        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(180)
        self.file_list.setToolTip('可拖入图片、图片文件夹或ZIP压缩包')

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        self.status_label = QLabel('待处理文件：0')
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)

        layout.addWidget(title)
        layout.addWidget(rule)
        layout.addLayout(button_row)
        layout.addWidget(self.output_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.file_list)
        layout.addWidget(self.progress)
        layout.addWidget(QLabel('处理日志：'))
        layout.addWidget(self.log_view)

        self.setCentralWidget(central)

        self.import_excel_btn.clicked.connect(self.open_import_dialog)
        self.add_images_btn.clicked.connect(self.select_images)
        self.add_folder_btn.clicked.connect(self.select_folder)
        self.clear_btn.clicked.connect(self.clear_files)
        self.output_btn.clicked.connect(self.select_output)
        self.start_btn.clicked.connect(self.start)

    def _append_log(self, message):
        text = self.logger.add(message)
        self.log_view.append(text)
        return text

    def open_import_dialog(self):
        service = self.runner.processor.service.project_service
        dialog = ImportDialog(service, self)
        if dialog.exec_() == QDialog.Accepted:
            count = len(service.list_projects())
            self._append_log('工程明细库当前共 {} 条。'.format(count))

    def select_images(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            '选择报告图片或ZIP',
            '',
            '报告文件 (*.jpg *.jpeg *.png *.bmp *.tif *.tiff *.zip)'
        )
        if paths:
            self.add_files(paths)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, '选择图片文件夹')
        if folder:
            self.add_files([folder])

    def add_files(self, files):
        collected = []

        for value in files:
            path = Path(value)
            try:
                collected.extend(self._collect_path(path))
            except Exception as exc:
                self._append_log('无法加载 {}：{}'.format(path, exc))

        existing = set(str(path.resolve()).lower() for path in self.files)
        added = 0

        for path in collected:
            resolved = path.resolve()
            key = str(resolved).lower()
            if key in existing:
                continue
            self.files.append(resolved)
            existing.add(key)
            self.file_list.addItem(str(resolved))
            added += 1

        self.status_label.setText('待处理文件：{}'.format(len(self.files)))
        self._append_log('新增 {} 个图片文件，当前共 {} 个。'.format(
            added,
            len(self.files)
        ))

    def _collect_path(self, path):
        if not path.exists():
            raise FileNotFoundError('路径不存在')

        if path.is_dir():
            return sorted(
                item
                for item in path.rglob('*')
                if item.is_file() and item.suffix.lower() in SUPPORTED_IMAGES
            )

        suffix = path.suffix.lower()

        if suffix in SUPPORTED_IMAGES:
            return [path]

        if suffix == '.zip':
            extracted = self._extract_zip(path)
            return self._collect_path(extracted)

        raise ValueError('不支持的文件类型: ' + suffix)

    def _extract_zip(self, zip_path):
        self.temp_root.mkdir(parents=True, exist_ok=True)
        target = Path(tempfile.mkdtemp(prefix='zip_', dir=str(self.temp_root)))
        target_text = str(target.resolve())

        with zipfile.ZipFile(str(zip_path), 'r') as archive:
            for info in archive.infolist():
                destination = (target / info.filename).resolve()

                try:
                    common = os.path.commonpath([
                        target_text,
                        str(destination),
                    ])
                except ValueError:
                    raise ValueError('ZIP包含不安全路径: ' + info.filename)

                if os.path.normcase(common) != os.path.normcase(target_text):
                    raise ValueError('ZIP包含不安全路径: ' + info.filename)

                archive.extract(info, str(target))

        self._append_log('ZIP已解压：{}'.format(zip_path.name))
        return target

    def clear_files(self):
        if self.thread and self.thread.isRunning():
            return
        self.files = []
        self.file_list.clear()
        self.status_label.setText('待处理文件：0')
        self.progress.setValue(0)
        self._append_log('已清空待处理列表。')

    def start(self):
        if not self.files:
            QMessageBox.information(self, '没有文件', '请先添加报告图片。')
            return

        project_count = len(
            self.runner.processor.service.project_service.list_projects()
        )
        if project_count <= 0:
            QMessageBox.warning(
                self,
                '未导入工程明细',
                '请先导入包含工程编号和工程名称的Excel文件。'
            )
            return

        self._set_processing(True)
        self.progress.setRange(0, 0)
        self._append_log('开始处理 {} 个文件。'.format(len(self.files)))

        self.thread = RunnerThread(self.runner, self.files)
        self.thread.completed.connect(self.on_finished)
        self.thread.failed.connect(self.on_failed)
        self.thread.start()

    def _set_processing(self, processing):
        for button in (
            self.import_excel_btn,
            self.add_images_btn,
            self.add_folder_btn,
            self.clear_btn,
            self.output_btn,
            self.start_btn,
        ):
            button.setEnabled(not processing)

    def on_finished(self, result):
        self.results = list(result or [])
        reviewed = self.review_pending_results(self.results)

        if reviewed:
            self.runner.save_results(self.results)

        success = sum(
            1 for item in self.results
            if item.get('status') == 'success'
        )
        pending = sum(
            1 for item in self.results
            if item.get('status') in ('review_required', 'unmatched')
        )
        failed = len(self.results) - success - pending

        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self._set_processing(False)
        self._append_log(
            '处理完成：成功 {}，待复核 {}，失败 {}。'.format(
                success,
                pending,
                failed
            )
        )

        QMessageBox.information(
            self,
            '处理完成',
            '成功：{}\n待复核：{}\n失败：{}\n输出目录：{}'.format(
                success,
                pending,
                failed,
                self.output_dir
            )
        )

    def review_pending_results(self, results):
        reviewed_count = 0
        rename_service = self.runner.processor.service

        for index, item in enumerate(list(results)):
            if item.get('status') not in ('review_required', 'unmatched'):
                continue

            candidates = item.get('candidates') or []
            if not candidates:
                self._append_log(
                    '无可用候选项目：' + item.get('source', '')
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
                    self._append_log(
                        '人工确认：{} -> {}'.format(
                            confirmed.get('source', ''),
                            confirmed.get('target', ''),
                        )
                    )

        return reviewed_count

    def on_failed(self, message):
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self._set_processing(False)
        self._append_log('处理失败：' + message)
        QMessageBox.critical(self, '处理失败', message)

    def select_output(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            '选择输出目录',
            str(self.output_dir)
        )

        if not directory:
            return ''

        self.output_dir = Path(directory).resolve()
        self.runner = FinalRunner(str(self.output_dir))
        self.output_label.setText('输出目录：' + str(self.output_dir))
        self._append_log('输出目录已设置为：' + str(self.output_dir))
        return str(self.output_dir)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [url.toLocalFile() for url in event.mimeData().urls()]
        self.add_files(paths)
        event.acceptProposedAction()
