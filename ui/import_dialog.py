# -*- coding: utf-8 -*-
"""
Excel import dialog.

UI layer delegates import operations to ProjectService.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QMessageBox
)

from ui.excel_loader import ExcelLoader


class ImportDialog(QDialog):

    def __init__(self, project_service=None):
        super().__init__()

        self.project_service = project_service
        self.preview_result = None
        self.loader = ExcelLoader()

        self.setWindowTitle('工程Excel导入')
        self.resize(800, 500)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.info = QLabel('请选择工程Excel文件')
        self.table = QTableWidget()

        self.select_btn = QPushButton('选择Excel文件')
        self.preview_btn = QPushButton('预览导入')
        self.confirm_btn = QPushButton('确认导入')

        layout.addWidget(self.info)
        layout.addWidget(self.table)
        layout.addWidget(self.select_btn)
        layout.addWidget(self.preview_btn)
        layout.addWidget(self.confirm_btn)

        self.setLayout(layout)

        self.select_btn.clicked.connect(self.select_excel)

    def select_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            '选择工程Excel',
            '',
            'Excel文件 (*.xlsx)'
        )

        if not file_path:
            return

        try:
            rows = self.loader.load(file_path)
            self.load_rows(rows)
            self.info.setText(
                '已加载: ' + file_path
            )
        except Exception as exc:
            QMessageBox.warning(
                self,
                '导入错误',
                str(exc)
            )

    def load_rows(self, rows):
        if not self.project_service:
            return None

        self.preview_result = self.project_service.preview_import(rows)

        items = self.preview_result.get('items', [])

        self.table.setRowCount(len(items))
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            '工程编号',
            '工程名称',
            '标准化名称'
        ])

        for row, item in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(item.get('project_code', '')))
            self.table.setItem(row, 1, QTableWidgetItem(item.get('project_name', '')))
            self.table.setItem(row, 2, QTableWidgetItem(item.get('normalized_name', '')))

        return self.preview_result

    def confirm_import(self):
        if not self.project_service or not self.preview_result:
            return 0

        return self.project_service.commit_import(
            self.preview_result.get('items', [])
        )

    def get_report(self):
        if not self.preview_result:
            return {}

        return self.preview_result.get('report', {})
