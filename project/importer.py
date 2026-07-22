# -*- coding: utf-8 -*-
"""
Excel project database importer.

Excel format:
工程编号 | 工程名称

Optional dependency:
openpyxl
"""

from pathlib import Path

from .database import ProjectDatabase
from .normalizer import ProjectNormalizer


class ProjectImporter:

    def __init__(self, db_path='data/projects.db'):
        self.db = ProjectDatabase(db_path)
        self.normalizer = ProjectNormalizer()

    def import_excel(self, excel_path):
        try:
            import openpyxl
        except ImportError:
            raise RuntimeError('缺少openpyxl模块')

        workbook = openpyxl.load_workbook(
            excel_path,
            read_only=True,
            data_only=True
        )

        sheet = workbook.active

        conn = self.db.connect()
        cursor = conn.cursor()

        count = 0

        for row in sheet.iter_rows(min_row=2, values_only=True):
            code, name = row[0], row[1]

            if not name:
                continue

            name = str(name).strip()
            code = str(code).strip() if code else ''

            cursor.execute(
                '''
                INSERT INTO projects
                (project_code, project_name, normalized_name)
                VALUES (?, ?, ?)
                ''',
                (
                    code,
                    name,
                    self.normalizer.normalize(name)
                )
            )

            count += 1

        conn.commit()
        conn.close()

        return count
