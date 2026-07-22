# -*- coding: utf-8 -*-
"""
Project library management window.

GUI layer only. Business operations are delegated to ProjectService.
"""


class ProjectManagerWindow:

    def __init__(self, project_service=None):
        self.project_service = project_service
        self.projects = []

    def load_projects(self):
        if not self.project_service:
            return []

        self.projects = self.project_service.list_projects()
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
