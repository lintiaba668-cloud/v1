# -*- coding: utf-8 -*-
"""
Excel import dialog logic.

UI layer delegates import operations to ProjectService.
"""


class ImportDialog:

    def __init__(self, project_service=None):
        self.project_service = project_service
        self.preview_result = None

    def load_rows(self, rows):
        if not self.project_service:
            return None

        self.preview_result = self.project_service.preview_import(rows)
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
