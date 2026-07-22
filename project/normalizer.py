# -*- coding: utf-8 -*-
"""
Project name normalizer.

Used before matching OCR project names with local project database.
"""

import re

from .alias_dictionary import get_aliases


class ProjectNormalizer:

    def __init__(self):
        self.aliases = get_aliases()

    def normalize(self, text):
        if not text:
            return ''

        text = text.strip()

        for old, new in self.aliases.items():
            text = text.replace(old, new)

        text = re.sub(r'\s+', '', text)
        text = text.replace('号', '#')

        return text
