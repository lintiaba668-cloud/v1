"""
PowerRename V1 主窗口
GUI层：负责交互、状态显示、Worker连接、项目库入口。
业务逻辑保持在 service / ocr 模块。
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QProgressBar
)

from ui.project_manager import ProjectManagerWindow
from ui.import_dialog import ImportDialog


SUPPORTED = {
    '.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.zip'
}


class MainWindow(QMainWindow):

    def __init__(self, project_service=None):
        super().__init__()

        self.worker = None
        self.project_service = project_service
        self.project_manager = ProjectManagerWindow(project_service)
        self.import_dialog = ImportDialog(project_service)

        self.setWindowTitle(
            'PowerRename V1 - 开竣工报告批量重命名工具'
        )
        self.resize(800, 600)
        self.setAcceptDrops(True)

        self.init_ui()

    def init_ui(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.info = QLabel(
            '请拖入 ZIP、图片文件或图片文件夹'
        )

        self.start_btn = QPushButton('开始处理')
        self.project_btn = QPushButton('项目库管理')
        self.import_btn = QPushButton('导入工程Excel')

        self.progress = QProgressBar()
        self.log = QTextEdit()
        self.log.setReadOnly(True)

        layout.addWidget(self.info)
        layout.addWidget(self.start_btn)
        layout.addWidget(self.project_btn)
        layout.addWidget(self.import_btn)
        layout.addWidget(self.progress)
        layout.addWidget(self.log)

        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.project_btn.clicked.connect(self.open_project_manager)
        self.import_btn.clicked.connect(self.open_import_dialog)

    def open_project_manager(self):
        self.log.append('打开项目库管理')
        self.project_manager.load_projects()

    def open_import_dialog(self):
        self.log.append('打开工程Excel导入')

    def attach_worker(self, worker):
        self.worker = worker

        worker.progress.connect(
            self.update_progress
        )

        worker.log.connect(
            self.append_log
        )

    def update_progress(self, current, total, filename):
        if total:
            self.progress.setValue(
                int(current * 100 / total)
            )

        self.info.setText(filename)

    def append_log(self, message):
        self.log.append(message)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = []

        for url in event.mimeData().urls():
            paths.append(Path(url.toLocalFile()))

        self.handle_drop(paths)

    def handle_drop(self, paths):
        self.log.clear()
        self.log.append('检测到拖入文件：')

        for path in paths:
            self.log.append(str(path))

            if path.is_dir():
                self.log.append('类型：图片文件夹')
            elif path.suffix.lower() in SUPPORTED:
                if path.suffix.lower() == '.zip':
                    self.log.append('类型：ZIP压缩包')
                else:
                    self.log.append('类型：图片文件')
            else:
                self.log.append('类型：不支持')

        self.info.setText(
            f'已添加 {len(paths)} 个任务'
        )
