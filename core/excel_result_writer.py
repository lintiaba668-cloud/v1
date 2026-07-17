"""
重命名结果Excel增强输出
"""

from openpyxl import Workbook


class ExcelResultWriter:
    def __init__(self):
        self.rows = []

    def add(self, result):
        self.rows.append(result)

    def save(self, filename):
        wb = Workbook()
        ws = wb.active
        ws.title = '处理结果'

        ws.append([
            '原文件',
            '工程名称',
            '工程编号',
            '新文件名',
            '状态'
        ])

        for row in self.rows:
            ws.append([
                row.get('source', row.get('file', '')),
                row.get('project_name', ''),
                row.get('project_code', ''),
                row.get('target', ''),
                row.get('status', '')
            ])

        wb.save(filename)
