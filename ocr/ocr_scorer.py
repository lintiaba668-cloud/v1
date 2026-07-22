# -*- coding: utf-8 -*-
"""
OCR result scoring module.

Used to select better OCR candidates when multiple preprocessing strategies
are available.
"""

import re


class OCRScorer:

    def score(self, fields, raw_text=''):
        score = 0

        project_name = fields.get('project_name', '') or ''
        project_code = fields.get('project_code', '') or ''

        if project_name:
            score += 40

            if len(project_name) >= 8:
                score += 10

        if project_code:
            score += 30

            if re.search(r'[A-Z0-9#-]{6,}', project_code):
                score += 10

        chinese = len(re.findall(r'[\u4e00-\u9fff]', raw_text))

        if chinese:
            score += min(chinese, 10)

        return score
