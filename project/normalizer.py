# -*- coding: utf-8 -*-
"""
Project name normalizer.

Used before matching OCR project names with local project database.
"""

import re


class ProjectNormalizer:

    def normalize(self, text):
        if not text:
            return ''

        text = text.strip()

        replacements = {
            '土庄变': '上庄变',
            '兰山': '栏山',
            '401杆': '#01杆',
            '4变': '#4变'
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        text = re.sub(r'\s+', '', text)
        text = text.replace('号', '#')

        return text
