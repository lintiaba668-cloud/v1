# -*- coding: utf-8 -*-
"""
Project service layer.

Provides unified project library operations for GUI and business logic.
"""

from .database import ProjectDatabase
from .import_manager import ProjectImportManager
from .backup import ProjectBackup


class ProjectService:

    def __init__(self, db_path='data/projects.db'):
        self.db = ProjectDatabase(db_path)
        self.import_manager = ProjectImportManager(db_path)
        self.backup_tool = ProjectBackup()

    def list_projects(self):
        return self.db.list_all()

    def find_by_code(self, code):
        return self.db.find_by_code(code)

    def preview_import(self, rows):
        return self.import_manager.preview(rows)

    def commit_import(self, items):
        return self.import_manager.commit(items)

    def backup(self, target_path):
        return self.backup_tool.backup(
            self.db.db_path,
            target_path
        )
