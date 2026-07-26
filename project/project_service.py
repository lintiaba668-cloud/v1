# -*- coding: utf-8 -*-
"""Project service layer."""

import threading

from core.resource import get_resource_path

from .database import ProjectDatabase
from .import_manager import ProjectImportManager
from .backup import ProjectBackup
from .match_manager import MatchManager


class ProjectService:

    def __init__(self, db_path=None):
        if db_path is None:
            db_path = get_resource_path('data/projects.db')

        self.db = ProjectDatabase(db_path)
        self.import_manager = ProjectImportManager(db_path)
        self.backup_tool = ProjectBackup()
        self.match_manager = MatchManager(project_service=self)
        self._cache_lock = threading.RLock()
        self._projects_cache = None
        self._project_code_index = None

    def _load_project_cache(self):
        if self._projects_cache is not None:
            return

        with self._cache_lock:
            if self._projects_cache is not None:
                return

            projects = self.db.list_all()
            self._projects_cache = projects
            self._project_code_index = {
                item.get('project_code', ''): item
                for item in projects
                if item.get('project_code')
            }

    def _invalidate_project_cache(self):
        with self._cache_lock:
            self._projects_cache = None
            self._project_code_index = None

    def list_projects(self):
        self._load_project_cache()
        return self._projects_cache

    def find_by_code(self, code):
        if not code:
            return None

        self._load_project_cache()
        project = self._project_code_index.get(code)
        if not project:
            return None

        return {
            'project_code': project.get('project_code', ''),
            'project_name': project.get('project_name', ''),
        }

    def preview_import(self, rows):
        return self.import_manager.preview(rows)

    def commit_import(self, items):
        count = self.import_manager.commit(items)
        self._invalidate_project_cache()
        return count

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
