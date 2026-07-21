# -*- coding: utf-8 -*-

"""Power industry OCR correction dictionary."""

import json
from pathlib import Path


class OCRDictionary:

    def __init__(self, path=None):
        self.mapping = {}
        if path:
            self.load(path)

    def load(self, path):
        try:
            data = json.loads(
                Path(path).read_text(encoding='utf-8')
            )
            self.mapping = data.get('mapping', {})
        except Exception:
            self.mapping = {}

    def correct(self, text):
        if not text:
            return ''

        result = text

        for wrong, right in self.mapping.items():
            result = result.replace(wrong, right)

        return result
