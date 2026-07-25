# -*- coding: utf-8 -*-
"""
Project detail matching manager.

Workflow:
OCR result -> normalize -> project library matching -> result report
"""

from difflib import SequenceMatcher


class MatchManager:

    def __init__(self, project_service=None, correction=None):
        self.project_service = project_service
        self.correction = correction

    def normalize_text(self, text):
        if not text:
            return ''

        value = str(text).strip()

        if self.correction:
            value = self.correction.correct(value)

        return value

    def calculate_score(self, source, target):
        source = self.normalize_text(source)
        target = self.normalize_text(target)

        if not source or not target:
            return 0

        return int(
            SequenceMatcher(
                None,
                source,
                target
            ).ratio() * 100
        )

    def match_project(self, ocr_text):
        """Match OCR text against project library."""

        if not self.project_service:
            return None

        projects = self.project_service.list_projects()

        best = None
        best_score = 0

        for project in projects:
            score = self.calculate_score(
                ocr_text,
                project.get('project_name', '')
            )

            if score > best_score:
                best_score = score
                best = project

        if not best:
            return {
                'status': 'unmatched',
                'score': 0
            }

        return {
            'status': 'matched' if best_score >= 80 else 'uncertain',
            'score': best_score,
            'project_code': best.get('project_code'),
            'project_name': best.get('project_name')
        }

    def batch_match(self, ocr_results):
        results = []

        for item in ocr_results:
            text = item.get('text', '')

            results.append(
                self.match_project(text)
            )

        return results
