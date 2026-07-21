# -*- coding: utf-8 -*-

"""Adaptive OCR region controller.

Expands OCR area when required fields cannot be found.
"""


class AdaptiveOCRRegion:

    def __init__(self, start=25, maximum=45, step=10):
        self.start = start
        self.maximum = maximum
        self.step = step

    def candidates(self):
        value = self.start

        while value <= self.maximum:
            yield value
            value += self.step

    def need_expand(self, fields):
        if not fields:
            return True

        return not (
            fields.get('project_name')
            or fields.get('project_code')
        )
