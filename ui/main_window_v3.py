# -*- coding: utf-8 -*-
"""PowerRename V1 main window.

PyQt5 / Win7 compatible workflow:
Excel project list -> images/folder/ZIP -> batch OCR -> Excel correction ->
renamed image output -> result workbook -> manual review when required.
"""

import os
from pathlib import Path
import tempfile
import time
import zipfile

from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QBrush, QColor
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

from core.cache_manager import clear_runtime_cache
from core.final_runner import FinalRunner
from core.resource import get_resource_path
from ui.ganzhi_date import MEMORIAL_GANZHI_DATE
from ui.import_dialog import ImportDialog
from ui.log_manager import LogManager
from ui.match_review_dialog import MatchReviewDialog


SUPPORTED_IMAGES = {
    '.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'
}
PROCESSED_ITEM_COLOR = '#cfefff'


def open_directory_in_explorer(directory, opener=None):
    """Open an existing output folder with Windows Explorer."""
    path = Path(directory).resolve()
    if not path.is_dir():
        raise FileNotFoundError('输出目录尚不存在：{}'.format(path))

    selected_opener = opener or getattr(os, 'startfile', None)
    if not callable(selected_opener):
        raise OSError('当前系统不支持打开文件夹')

    selected_opener(str(path))
    return str(path)


def format_elapsed_time(seconds):
    total = max(0, int(seconds or 0))
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours:
        return '{:02d}:{:02d}:{:02d}'.format(
            hours,
            minutes,
            seconds,
        )

    return '{:02d}:{:02d}'.format(minutes, seconds)


class RunnerThread(QThread):

    completed = pyqtSignal(object)
    failed = pyqtSignal(str)
    progress = pyqtSignal(int, int, str)
    stage_progress = pyqtSignal(str, int, int, int)

    def __init__(self, runner, files):
        super().__init__()
        self.runner = runner
        self.files = list(files)

    def run(self):
        try:
            self.completed.emit(self.runner.run(
                self.files,
                progress_callback=self.progress.emit,
                stage_callback=self.stage_progress.emit,
            ))
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
        self.output_dir = self.runner.output_dir.resolve()
        self.temp_root = get_resource_path('temp/imported').resolve()
        self._output_dir_manually_selected = False
        self._batch_started_at = None
        self._elapsed_seconds = 0.0
        self._difficult_count = 0

        self.setWindowTitle('PowerRename V1 - 开竣工报告批量重命名')
        self.resize(960, 680)
        self.setAcceptDrops(True)
        self._build_ui()
        self.elapsed_timer = QTimer(self)
        self.elapsed_timer.setInterval(250)
        self.elapsed_timer.timeout.connect(self._update_elapsed_time)
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
        self.open_output_btn = QPushButton('打开输出目录')
        self.start_btn = QPushButton('3. 开始批量处理')
        self.cache_btn = QPushButton('缓存清理')

        button_row.addWidget(self.import_excel_btn)
        button_row.addWidget(self.add_images_btn)
        button_row.addWidget(self.add_folder_btn)
        button_row.addWidget(self.clear_btn)
        output_column = QVBoxLayout()
        output_column.setContentsMargins(0, 0, 0, 0)
        output_column.setSpacing(3)
        output_column.addWidget(self.output_btn)
        output_column.addWidget(self.open_output_btn)
        button_row.addLayout(output_column)
        action_column = QVBoxLayout()
        action_column.setContentsMargins(0, 0, 0, 0)
        action_column.setSpacing(3)
        action_column.addWidget(self.start_btn)
        action_column.addWidget(self.cache_btn)
        button_row.addLayout(action_column)

        self.output_label = QLabel(
            '输出目录：添加图片后自动设为同目录下的“输出文件夹”'
        )
        self.output_label.setWordWrap(True)

        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(180)
        self.file_list.setToolTip('可拖入图片、图片文件夹或ZIP压缩包')

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress_percent_label = QLabel('0%')
        self.progress_percent_label.setMinimumWidth(46)
        self.progress_percent_label.setAlignment(Qt.AlignCenter)
        progress_row = QHBoxLayout()
        progress_row.setContentsMargins(0, 0, 0, 0)
        progress_row.addWidget(self.progress)
        progress_row.addWidget(self.progress_percent_label)

        self.status_label = QLabel('待处理文件：0    已处理：0')
        self.phase_label = QLabel('识别阶段：等待开始')
        self.elapsed_label = QLabel('运行时间：00:00')
        self.memorial_date_label = QLabel(MEMORIAL_GANZHI_DATE)
        self.memorial_date_label.setStyleSheet(
            'color: #5b6670; font-family: "Microsoft YaHei"; '
            'font-size: 13px; letter-spacing: 1px;'
        )
        self.memorial_date_label.setToolTip('固定纪念日期')
        self.memorial_signature_label = QLabel('Lzz')
        self.memorial_signature_label.setStyleSheet(
            'color: #2f6f9f; font-family: "Segoe UI"; '
            'font-size: 15px; font-weight: 600; '
            'padding: 0 5px 1px 5px; '
            'border-bottom: 1px solid #9fbfd4;'
        )
        memorial_row = QHBoxLayout()
        memorial_row.setContentsMargins(0, 0, 4, 0)
        memorial_row.addStretch(1)
        memorial_row.addWidget(self.memorial_date_label)
        memorial_row.addSpacing(14)
        memorial_row.addWidget(self.memorial_signature_label)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)

        layout.addWidget(title)
        layout.addWidget(rule)
        layout.addLayout(button_row)
        layout.addWidget(self.output_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.phase_label)
        layout.addWidget(self.elapsed_label)
        layout.addLayout(memorial_row)
        layout.addWidget(self.file_list)
        layout.addLayout(progress_row)
        layout.addWidget(QLabel('处理日志：'))
        layout.addWidget(self.log_view)

        self.setCentralWidget(central)

        self.import_excel_btn.clicked.connect(self.open_import_dialog)
        self.add_images_btn.clicked.connect(self.select_images)
        self.add_folder_btn.clicked.connect(self.select_folder)
        self.clear_btn.clicked.connect(self.clear_files)
        self.output_btn.clicked.connect(self.select_output)
        self.open_output_btn.clicked.connect(self.open_output_directory)
        self.start_btn.clicked.connect(self.start)
        self.cache_btn.clicked.connect(self.clear_cache)
        self._refresh_open_output_button()

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
        input_values = list(files)
        was_empty = not self.files
        collected = []

        for value in input_values:
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

        self._update_file_counts(0, len(self.files))
        if added:
            if (
                was_empty
                and not self._output_dir_manually_selected
                and input_values
            ):
                self._set_output_dir(
                    self._default_output_dir_for_source(
                        Path(input_values[0])
                    ),
                    manual=False,
                )
            self._reset_progress_display(reset_highlights=True)
        self._append_log('新增 {} 个图片文件，当前共 {} 个。'.format(
            added,
            len(self.files)
        ))

    def _collect_path(self, path):
        if not path.exists():
            raise FileNotFoundError('路径不存在')

        if path.is_dir():
            default_output = (
                path.resolve() / '输出文件夹'
            ).resolve()
            excluded = [default_output, self.output_dir.resolve()]
            return sorted(
                item
                for item in path.rglob('*')
                if (
                    item.is_file()
                    and item.suffix.lower() in SUPPORTED_IMAGES
                    and not any(
                        self._path_is_inside(item, value)
                        for value in excluded
                    )
                )
            )

        suffix = path.suffix.lower()

        if suffix in SUPPORTED_IMAGES:
            return [path]

        if suffix == '.zip':
            extracted = self._extract_zip(path)
            return self._collect_path(extracted)

        raise ValueError('不支持的文件类型: ' + suffix)

    @staticmethod
    def _default_output_dir_for_source(source):
        path = Path(source).resolve()
        base = path if path.is_dir() else path.parent
        return (base / '输出文件夹').resolve()

    @staticmethod
    def _path_is_inside(path, directory):
        try:
            return os.path.normcase(os.path.commonpath([
                str(Path(path).resolve()),
                str(Path(directory).resolve()),
            ])) == os.path.normcase(str(Path(directory).resolve()))
        except ValueError:
            return False

    def _set_output_dir(self, directory, manual):
        self.output_dir = Path(directory).resolve()
        self.runner = FinalRunner(str(self.output_dir))
        self.output_label.setText('输出目录：' + str(self.output_dir))
        if manual:
            self._output_dir_manually_selected = True
        self._refresh_open_output_button()
        self._append_log('输出目录已设为：{}'.format(self.output_dir))

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
        self._update_file_counts(0, 0)
        self._reset_progress_display(reset_highlights=False)
        self._reset_elapsed_time()
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
        self._reset_progress_display(reset_highlights=True)
        self._update_file_counts(0, len(self.files))
        self._start_elapsed_time()
        self._append_log('开始处理 {} 个文件。'.format(len(self.files)))

        self.thread = RunnerThread(self.runner, self.files)
        self.thread.progress.connect(self.on_progress)
        self.thread.stage_progress.connect(self.on_stage_progress)
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
            self.cache_btn,
        ):
            button.setEnabled(not processing)
        self.open_output_btn.setEnabled(
            not processing and self.output_dir.is_dir()
        )

    def on_finished(self, result):
        self._stop_elapsed_time()
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
        self.progress_percent_label.setText('100%')
        self._update_file_counts(len(self.files), len(self.files))
        self.phase_label.setText(
            '识别阶段：已完成（精细识别 {} 张）'.format(
                self._difficult_count
            )
        )
        self._set_processing(False)
        self._refresh_open_output_button()
        self._append_log(
            '处理完成：成功 {}，待复核 {}，失败 {}，用时 {}。'.format(
                success,
                pending,
                failed,
                format_elapsed_time(self._elapsed_seconds),
            )
        )

        QMessageBox.information(
            self,
            '处理完成',
            '成功：{}\n待复核：{}\n失败：{}\n用时：{}\n输出目录：{}'.format(
                success,
                pending,
                failed,
                format_elapsed_time(self._elapsed_seconds),
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
        self._stop_elapsed_time()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress_percent_label.setText('0%')
        self._set_processing(False)
        self._append_log('处理失败：' + message)
        QMessageBox.critical(self, '处理失败', message)

    def on_progress(self, current, total, filename):
        total = max(0, int(total or 0))
        current = max(0, min(int(current or 0), total))
        percent = int(current * 100 / total) if total else 0

        self.progress.setRange(0, 100)
        self.progress.setValue(percent)
        self.progress_percent_label.setText('{}%'.format(percent))
        self._update_file_counts(current, total)
        self._mark_file_processed(filename)

    def on_stage_progress(self, stage, current, total, difficult_count):
        current = max(0, int(current or 0))
        total = max(0, int(total or 0))
        difficult_count = max(0, int(difficult_count or 0))

        if stage == 'fast':
            self._difficult_count = difficult_count
            self.phase_label.setText(
                '识别阶段：快速识别 {}/{}    困难队列：{}'.format(
                    min(current, total),
                    total,
                    difficult_count,
                )
            )
        elif stage == 'deep':
            self._difficult_count = max(
                self._difficult_count,
                total,
            )
            self.phase_label.setText(
                '识别阶段：精细识别 {}/{}    剩余：{}'.format(
                    min(current, total),
                    total,
                    difficult_count,
                )
            )
        elif stage == 'complete':
            self.phase_label.setText(
                '识别阶段：识别完成，准备人工复核'
            )

    def _update_file_counts(self, processed=0, total=None):
        if total is None:
            total = len(self.files)

        total = max(0, int(total or 0))
        processed = max(0, min(int(processed or 0), total))
        remaining = total - processed
        self.status_label.setText(
            '待处理文件：{}    已处理：{}'.format(remaining, processed)
        )

    def _mark_file_processed(self, filename):
        target = os.path.normcase(os.path.abspath(str(filename)))

        for index in range(self.file_list.count()):
            item = self.file_list.item(index)
            item_path = os.path.normcase(os.path.abspath(item.text()))
            if item_path == target:
                item.setBackground(QBrush(QColor(PROCESSED_ITEM_COLOR)))
                return

    def _reset_progress_display(self, reset_highlights=True):
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress_percent_label.setText('0%')
        self._difficult_count = 0
        if hasattr(self, 'phase_label'):
            self.phase_label.setText('识别阶段：等待开始')

        if not reset_highlights:
            return

        for index in range(self.file_list.count()):
            self.file_list.item(index).setBackground(QBrush())

    def _start_elapsed_time(self):
        self._batch_started_at = time.monotonic()
        self._elapsed_seconds = 0.0
        self.elapsed_label.setText('运行时间：00:00')
        self.elapsed_timer.start()

    def _update_elapsed_time(self):
        if self._batch_started_at is None:
            return

        self._elapsed_seconds = time.monotonic() - self._batch_started_at
        self.elapsed_label.setText(
            '运行时间：' + format_elapsed_time(self._elapsed_seconds)
        )

    def _stop_elapsed_time(self):
        self._update_elapsed_time()
        self.elapsed_timer.stop()
        self._batch_started_at = None

    def _reset_elapsed_time(self):
        if hasattr(self, 'elapsed_timer'):
            self.elapsed_timer.stop()
        self._batch_started_at = None
        self._elapsed_seconds = 0.0
        self.elapsed_label.setText('运行时间：00:00')

    def select_output(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            '选择输出目录',
            str(self.output_dir)
        )

        if not directory:
            return ''

        self._set_output_dir(directory, manual=True)
        return str(self.output_dir)

    def _refresh_open_output_button(self):
        self.open_output_btn.setEnabled(self.output_dir.is_dir())

    def open_output_directory(self):
        try:
            opened = open_directory_in_explorer(self.output_dir)
        except Exception as exc:
            self._refresh_open_output_button()
            self._append_log('打开输出目录失败：{}'.format(exc))
            QMessageBox.warning(
                self,
                '无法打开输出目录',
                str(exc),
            )
            return ''

        self._append_log('已打开输出目录：{}'.format(opened))
        return opened

    def clear_cache(self):
        if self.thread and self.thread.isRunning():
            return

        reply = QMessageBox.question(
            self,
            '清理缓存',
            '将清理 OCR 裁切图和 ZIP 临时文件。\n'
            '不会删除工程库、运行日志和输出图片。是否继续？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            summary = clear_runtime_cache(
                protected_paths=self.files,
            )
        except Exception as exc:
            self._append_log('缓存清理失败：{}'.format(exc))
            QMessageBox.critical(
                self,
                '缓存清理失败',
                str(exc),
            )
            return

        removed = int(summary.get('files_removed', 0))
        removed_mb = (
            float(summary.get('bytes_removed', 0)) / 1024.0 / 1024.0
        )
        skipped = summary.get('skipped') or []
        message = '已清理 {} 个缓存文件，共 {:.2f} MB。'.format(
            removed,
            removed_mb,
        )
        if skipped:
            message += (
                '\n当前列表包含 ZIP 临时图片，相关目录已安全跳过；'
                '清空待处理列表后可再次清理。'
            )

        self._append_log(message.replace('\n', ' '))
        QMessageBox.information(self, '缓存清理完成', message)
        self._append_log('输出目录已设置为：' + str(self.output_dir))
        return str(self.output_dir)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [url.toLocalFile() for url in event.mimeData().urls()]
        self.add_files(paths)
        event.acceptProposedAction()
