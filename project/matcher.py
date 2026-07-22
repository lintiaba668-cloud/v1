# -*- coding: utf-8 -*-

from difflib import SequenceMatcher

from .normalizer import ProjectNormalizer


class ProjectMatcher:

    def __init__(self):
        self.normalizer = ProjectNormalizer()

    def score(self, ocr_name, db_name):
        a = self.normalizer.normalize(ocr_name)
        b = self.normalizer.normalize(db_name)

        if not a or not b:
            return 0

        return SequenceMatcher(None, a, b).ratio() * 100
