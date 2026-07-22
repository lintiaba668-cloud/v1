# -*- coding: utf-8 -*-
"""
Power engineering project matcher.

Domain weighted matcher with conflict penalties.
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

        score += self._field_match(
            ocr,
            std,
            r'.{0,30}(\d+kV.*?变)',
            30
        )

        score += self._field_match(
            ocr,
            std,
            r'(\d+kV.*?线)',
            30
        )

        pole_result = self._pole_score(ocr, std)
        score += pole_result

        if self._contains_voltage(ocr, std):
            score += 10
        elif self._has_voltage_conflict(ocr, std):
            score -= 20

        return max(0, min(score, 100))

    def _field_match(self, a, b, pattern, weight):
        ma = set(re.findall(pattern, a))
        mb = set(re.findall(pattern, b))

        if ma and mb and ma & mb:
            return weight

        return 0

    def _pole_score(self, a, b):
        poles_a = set(re.findall(r'#?\d+杆', a))
        poles_b = set(re.findall(r'#?\d+杆', b))

        if not poles_a or not poles_b:
            return 0

        if poles_a & poles_b:
            return 25

        # Same line but different pole is a strong negative signal
        return -40

    def _contains_voltage(self, a, b):
        levels_a = set(re.findall(r'\d+kV', a))
        levels_b = set(re.findall(r'\d+kV', b))
        return bool(levels_a & levels_b)

    def _has_voltage_conflict(self, a, b):
        levels_a = set(re.findall(r'\d+kV', a))
        levels_b = set(re.findall(r'\d+kV', b))
        return bool(levels_a and levels_b and not levels_a & levels_b)
