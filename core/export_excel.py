"""
Excel导出模块
"""

from openpyxl import Workbook


def export_results(results, filename):
    wb = Workbook()
    ws = wb.active
    ws.title = '重命名记录'

    ws.append([
        '原文件',
        '工程名称',
        '工程编号',
        '新文件名',
        '状态'
    ])

    for item in results:
        ws.append([
            item.get('source', ''),
            item.get('project_name', ''),
            item.get('project_code', ''),
            item.get('target', ''),
            item.get('status', '')
        ])

    wb.save(filename)
