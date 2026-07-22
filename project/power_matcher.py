# -*- coding: utf-8 -*-
"""
Power engineering project matcher.

A domain-specific matcher for electric power project names.
"""

import re

from .normalizer import ProjectNormalizer


class PowerProjectMatcher:

    def __init__(self):
        self.normalizer = ProjectNormalizer()

    def score(self, ocr_name, standard_name):
        if not ocr_name or not standard_name:
            return 0

        ocr = self.normalizer.normalize(ocr_name)
        std = self.normalizer.normalize(standard_name)

        score = 0

        # Substation name
        score += self._keyword_score(
            ocr,
            std,
            r'.{0,20}(\d+kV.*?变)'
        ) * 30

        # Line name
        score += self._keyword_score(
            ocr,
            std,
            r'(\d+kV.*?线)'
        ) * 30

        # Pole number
        score += self._keyword_score(
            ocr,
            std,
            r'(#?\d+杆)'
        ) * 25

        # Voltage level
        if self._contains_voltage(ocr, std):
            score += 10

        return min(score, 100)

    def _keyword_score(self, a, b, pattern):
        ma = re.findall(pattern, a)
        mb = re.findall(pattern, b)

        if not ma or not mb:
            return 0

        return 1 if set(ma) & set(mb) else 0

    def _contains_voltage(self, a, b):
        levels_a = set(re.findall(r'\d+kV', a))
        levels_b = set(re.findall(r'\d+kV', b))
        return bool(levels_a & levels_b)
