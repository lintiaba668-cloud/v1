# -*- coding: utf-8 -*-

from .database import ProjectDatabase
from .matcher import ProjectMatcher
from .model import MatchResult


class ProjectResolver:

    def __init__(self, db_path='data/projects.db'):
        self.db = ProjectDatabase(db_path)
        self.matcher = ProjectMatcher()

    def resolve(self, project_name='', project_code=''):

        # 1. project code exact match
        result = self.db.find_by_code(project_code)

        if result:
            return MatchResult(
                project_name=result['project_name'],
                project_code=result['project_code'],
                matched=True,
                score=100,
                source='code'
            )

        # 2. project name fuzzy matching
        if project_name:
            best = None
            best_score = 0

            for item in self.db.list_all():
                score = self.matcher.score(
                    project_name,
                    item['project_name']
                )

                if score > best_score:
                    best_score = score
                    best = item

            # Conservative threshold
            if best and best_score >= 75:
                return MatchResult(
                    project_name=best['project_name'],
                    project_code=best['project_code'],
                    matched=True,
                    score=best_score,
                    source='name'
                )

        # 3. keep OCR result
        return MatchResult(
            project_name=project_name,
            project_code=project_code,
            matched=False,
            score=0,
            source='ocr'
        )
