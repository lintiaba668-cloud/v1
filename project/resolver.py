# -*- coding: utf-8 -*-

from .database import ProjectDatabase
from .matcher import ProjectMatcher
from .model import MatchResult


class ProjectResolver:

    def __init__(self, db_path='data/projects.db'):
        self.db = ProjectDatabase(db_path)
        self.matcher = ProjectMatcher()

    def resolve(self, project_name='', project_code=''):

        # 1. code exact match
        result = self.db.find_by_code(project_code)

        if result:
            return MatchResult(
                project_name=result['project_name'],
                project_code=result['project_code'],
                matched=True,
                score=100,
                source='code'
            )

        # 2. name matching reserved for next stage
        return MatchResult(
            project_name=project_name,
            project_code=project_code,
            matched=False,
            score=0,
            source='ocr'
        )
