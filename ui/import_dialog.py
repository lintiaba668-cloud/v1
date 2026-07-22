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
    QTableWidgetItem
)


class ImportDialog(QDialog):

    def __init__(self, project_service=None):
        super().__init__()

        self.project_service = project_service
        self.preview_result = None

        self.setWindowTitle('工程Excel导入')
        self.resize(800, 500)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.info = QLabel('请选择工程Excel文件')
        self.table = QTableWidget()

        self.preview_btn = QPushButton('预览导入')
        self.confirm_btn = QPushButton('确认导入')

        layout.addWidget(self.info)
        layout.addWidget(self.table)
        layout.addWidget(self.preview_btn)
        layout.addWidget(self.confirm_btn)

        self.setLayout(layout)

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
            self.table.setItem(
                row, 0,
                QTableWidgetItem(item.get('project_code', ''))
            )
            self.table.setItem(
                row, 1,
                QTableWidgetItem(item.get('project_name', ''))
            )
            self.table.setItem(
                row, 2,
                QTableWidgetItem(item.get('normalized_name', ''))
            )

        return self.preview_result

    def confirm_import(self):
        if not self.project_service or not self.preview_result:
            return 0

        items = self.preview_result.get('items', [])

        return self.project_service.commit_import(items)

    def get_report(self):
        if not self.preview_result:
            return {}

        return self.preview_result.get('report', {})
