# -*- coding: utf-8 -*-
"""Manual review dialog for uncertain project-detail matches."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class MatchReviewDialog(QDialog):
    """Let the operator select one imported project candidate safely."""

    def __init__(self, rename_service, review_item, parent=None):
        super().__init__(parent)
        self.rename_service = rename_service
        self.review_item = dict(review_item or {})
        self.confirmed_result = None

        self.setWindowTitle('人工复核工程匹配')
        self.resize(900, 520)
        self._build_ui()
        self._load_candidates()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        source = self.review_item.get('source', '')
        ocr_name = self.review_item.get('ocr_project_name', '')
        ocr_code = self.review_item.get('ocr_project_code', '')
        score = self.review_item.get('match_score', 0.0)
        margin = self.review_item.get('match_margin', 0.0)

        self.source_label = QLabel('原文件：' + source)
        self.ocr_label = QLabel(
            'OCR工程：{}  编号：{}  最高分：{}  分差：{}'.format(
                ocr_name or '未识别',
                ocr_code or '未识别',
                score,
                margin,
            )
        )
        self.ocr_label.setWordWrap(True)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            '工程编号',
            '工程名称',
            '匹配分数',
            '评分说明',
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.confirm_selection)

        button_layout = QHBoxLayout()
        self.confirm_button = QPushButton('确认并重命名')
        self.skip_button = QPushButton('暂不处理')
        self.confirm_button.clicked.connect(self.confirm_selection)
        self.skip_button.clicked.connect(self.reject)
        button_layout.addStretch(1)
        button_layout.addWidget(self.confirm_button)
        button_layout.addWidget(self.skip_button)

        layout.addWidget(self.source_label)
        layout.addWidget(self.ocr_label)
        layout.addWidget(self.table)
        layout.addLayout(button_layout)

    def _load_candidates(self):
        candidates = list(self.review_item.get('candidates') or [])

        if not candidates:
            QMessageBox.information(
                self,
                '没有候选项目',
                '当前结果没有可供确认的候选项目。',
            )
            self.confirm_button.setEnabled(False)
            return

        self.table.setRowCount(len(candidates))

        for row, candidate in enumerate(candidates):
            code = candidate.get('project_code', '')
            name = candidate.get('project_name', '')
            score = candidate.get('score', 0.0)
            breakdown = candidate.get('breakdown', {}) or {}
            breakdown_text = '，'.join(
                '{}:{}'.format(key, value)
                for key, value in sorted(breakdown.items())
            )

            code_item = QTableWidgetItem(str(code))
            name_item = QTableWidgetItem(str(name))
            score_item = QTableWidgetItem(str(score))
            detail_item = QTableWidgetItem(breakdown_text)

            code_item.setData(Qt.UserRole, str(code))
            self.table.setItem(row, 0, code_item)
            self.table.setItem(row, 1, name_item)
            self.table.setItem(row, 2, score_item)
            self.table.setItem(row, 3, detail_item)

        self.table.resizeColumnsToContents()
        self.table.selectRow(0)

    def confirm_selection(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, '未选择项目', '请选择一个工程项目。')
            return

        code_item = self.table.item(row, 0)
        project_code = code_item.data(Qt.UserRole) if code_item else ''

        result = self.rename_service.confirm_review(
            self.review_item,
            project_code,
        )

        if result.get('status') != 'success':
            QMessageBox.warning(
                self,
                '确认失败',
                result.get('error', '人工确认失败'),
            )
            return

        self.confirmed_result = result
        self.accept()
