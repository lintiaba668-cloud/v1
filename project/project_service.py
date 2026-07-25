# -*- coding: utf-8 -*-
"""
Project service layer.

Provides unified project library operations for GUI and business logic.
"""

from .database import ProjectDatabase
from .import_manager import ProjectImportManager
from .backup import ProjectBackup
from .match_manager import MatchManager


class ProjectService:

    def __init__(self, db_path='data/projects.db'):
        self.db = ProjectDatabase(db_path)
        self.import_manager = ProjectImportManager(db_path)
        self.backup_tool = ProjectBackup()
        self.match_manager = MatchManager(project_service=self)

    def list_projects(self):
        return self.db.list_all()

    def find_by_code(self, code):
        return self.db.find_by_code(code)

    def preview_import(self, rows):
        return self.import_manager.preview(rows)

    def commit_import(self, items):
        return self.import_manager.commit(items)

    def match_project(self, project_name='', project_code=''):
        """Match one OCR result against imported project details."""

        return self.match_manager.match_project(
            ocr_text=project_name,
            project_code=project_code
        )

    def batch_match_projects(self, ocr_results):
        """Match a batch of OCR results while preserving input order."""

        return self.match_manager.batch_match(ocr_results)

    def backup(self, target_path):
        return self.backup_tool.backup(
            self.db.db_path,
            target_path
        )
