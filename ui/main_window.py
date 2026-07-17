"""
PowerRename V1 主窗口
第一阶段 GUI 框架
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QLabel, QPushButton, QTextEdit,
    QProgressBar
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PowerRename V1 - 开竣工报告批量重命名工具')
        self.resize(800, 600)
        self.init_ui()

    def init_ui(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.info = QLabel('请拖入 ZIP、图片文件或图片文件夹')
        self.start_btn = QPushButton('开始处理')
        self.progress = QProgressBar()
        self.log = QTextEdit()
        self.log.setReadOnly(True)

        layout.addWidget(self.info)
        layout.addWidget(self.start_btn)
        layout.addWidget(self.progress)
        layout.addWidget(self.log)

        widget.setLayout(layout)
        self.setCentralWidget(widget)
