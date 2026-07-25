# -*- coding: utf-8 -*-
"""Backward-compatible power engineering project matcher.

The old matcher used several exact regular-expression fields and produced a
score of only 35 for known OCR-error samples. Reuse the production matching
strategy so tests and runtime decisions use the same domain rules.
"""

from .match_strategy import PowerProjectMatchStrategy


class PowerProjectMatcher:

    def __init__(self):
        self.strategy = PowerProjectMatchStrategy()

    def score(self, ocr_name, standard_name):
        return self.strategy.score(
            ocr_name,
            standard_name,
        ).get('score', 0.0)
