# -*- coding: utf-8 -*-
"""
Project import manager.

Production import workflow:
Excel -> validate -> duplicate check -> normalize -> preview -> commit
"""

from .database import ProjectDatabase
from .normalizer import ProjectNormalizer
from .validator import ProjectValidator
from .import_report import ImportReport


class ProjectImportManager:

    def __init__(self, db_path='data/projects.db'):
        self.db = ProjectDatabase(db_path)
        self.normalizer = ProjectNormalizer()
        self.validator = ProjectValidator()

    def preview(self, rows):
        report = ImportReport()
        preview_data = []

        existing = {
            item['project_code']
            for item in self.db.list_all()
        }

        for index, row in enumerate(rows, start=1):
            code = str(row[0]).strip() if row[0] else ''
            name = str(row[1]).strip() if row[1] else ''

            check = self.validator.validate(code, name)

            if not check['valid']:
                report.add_failed(index, check['errors'])
                continue

            if code and code in existing:
                report.add_duplicate(index)
                continue

            preview_data.append({
                'project_code': code,
                'project_name': name,
                'normalized_name': self.normalizer.normalize(name)
            })

        return {
            'items': preview_data,
            'report': report.to_dict()
        }

    def commit(self, items):
        conn = self.db.connect()
        cursor = conn.cursor()

        for item in items:
            cursor.execute(
                '''
                INSERT INTO projects
                (project_code, project_name, normalized_name)
                VALUES (?, ?, ?)
                ''',
                (
                    item['project_code'],
                    item['project_name'],
                    item['normalized_name']
                )
            )

        conn.commit()
        conn.close()

        return len(items)
