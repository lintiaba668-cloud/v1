# -*- coding: utf-8 -*-

"""Adaptive OCR region controller.

开工报告的工程名称通常位于页面顶部约 8%~16%，竣工报告名称和编号
位于顶部表格。28% 可覆盖两类核心字段，同时避免大量工程量正文干扰。
"""


class AdaptiveOCRRegion:

    def __init__(self, start=28, maximum=40, step=6):
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
