# -*- coding: utf-8 -*-
"""Excel project-detail import dialog."""

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QMessageBox,
)

from ui.excel_loader import ExcelLoader


class ImportDialog(QDialog):

    def __init__(self, project_service=None, parent=None):
        super().__init__(parent)

        self.project_service = project_service
        self.preview_result = None
        self.rows = []
        self.loader = ExcelLoader()

        self.setWindowTitle('导入工程明细 Excel')
        self.resize(900, 520)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.info = QLabel(
            'Excel格式：第一列为工程编号，第二列为工程名称，第一行为表头。'
        )
        self.info.setWordWrap(True)
        self.table = QTableWidget()

        button_layout = QHBoxLayout()
        self.select_btn = QPushButton('选择Excel文件')
        self.preview_btn = QPushButton('重新预览')
        self.confirm_btn = QPushButton('确认导入')
        self.cancel_btn = QPushButton('关闭')

        button_layout.addWidget(self.select_btn)
        button_layout.addWidget(self.preview_btn)
        button_layout.addStretch(1)
        button_layout.addWidget(self.confirm_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addWidget(self.info)
        layout.addWidget(self.table)
        layout.addLayout(button_layout)

        self.select_btn.clicked.connect(self.select_excel)
        self.preview_btn.clicked.connect(self.preview_import)
        self.confirm_btn.clicked.connect(self.confirm_import)
        self.cancel_btn.clicked.connect(self.reject)

        self.preview_btn.setEnabled(False)
        self.confirm_btn.setEnabled(False)

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
            self.rows = self.loader.load(file_path)
            self.info.setText('已加载：{}，共 {} 行。'.format(
                file_path,
                len(self.rows)
            ))
            self.preview_btn.setEnabled(True)
            self.preview_import()
        except Exception as exc:
            QMessageBox.warning(self, '导入错误', str(exc))

    def preview_import(self):
        if not self.project_service:
            QMessageBox.warning(self, '导入错误', '项目服务未初始化。')
            return None

        if not self.rows:
            QMessageBox.information(self, '没有数据', 'Excel中没有可导入的数据。')
            return None

        self.preview_result = self.project_service.preview_import(self.rows)
        items = self.preview_result.get('items', [])
        report = self.preview_result.get('report', {})

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

        self.table.resizeColumnsToContents()
        self.confirm_btn.setEnabled(bool(items))

        self.info.setText(
            '可导入 {} 条；重复 {} 条；无效 {} 条。'.format(
                len(items),
                len(report.get('duplicate', [])),
                len(report.get('failed', []))
            )
        )
        return self.preview_result

    def load_rows(self, rows):
        """测试及外部调用兼容入口。"""
        self.rows = list(rows or [])
        return self.preview_import()

    def confirm_import(self):
        if not self.project_service or not self.preview_result:
            return 0

        items = self.preview_result.get('items', [])
        if not items:
            return 0

        try:
            count = self.project_service.commit_import(items)
        except Exception as exc:
            QMessageBox.warning(self, '导入失败', str(exc))
            return 0

        QMessageBox.information(
            self,
            '导入完成',
            '成功导入 {} 条工程明细。'.format(count)
        )
        self.accept()
        return count

    def get_report(self):
        if not self.preview_result:
            return {}
        return self.preview_result.get('report', {})
