# -*- coding: utf-8 -*-
"""
Project library management window.

GUI layer only. Business operations are delegated to ProjectService.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLabel
)


class ProjectManagerWindow(QWidget):

    def __init__(self, project_service=None):
        super().__init__()

        self.project_service = project_service
        self.projects = []

        self.setWindowTitle('工程项目库管理')
        self.resize(700, 500)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.info = QLabel('项目库')
        self.table = QTableWidget()

        self.refresh_btn = QPushButton('刷新项目库')
        self.backup_btn = QPushButton('备份项目库')

        layout.addWidget(self.info)
        layout.addWidget(self.table)
        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.backup_btn)

        self.setLayout(layout)

        self.refresh_btn.clicked.connect(self.load_projects)

    def load_projects(self):
        if not self.project_service:
            return []

        self.projects = self.project_service.list_projects()

        self.table.setRowCount(len(self.projects))
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            '工程编号',
            '工程名称',
            '标准化名称'
        ])

        for row, item in enumerate(self.projects):
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

        return self.projects

    def preview_import(self, rows):
        if not self.project_service:
            return None

        return self.project_service.preview_import(rows)

    def commit_import(self, items):
        if not self.project_service:
            return 0

        return self.project_service.commit_import(items)

    def backup_database(self, target_path):
        if not self.project_service:
            return None

        return self.project_service.backup(target_path)
