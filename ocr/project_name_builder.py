# -*- coding: utf-8 -*-

"""Project name reconstruction for power engineering documents.

Uses longest dictionary matching to restore split OCR characters.
"""

import json
from pathlib import Path
import re


class ProjectNameBuilder:

    def __init__(self, dictionary_path=None):
        self.terms = []

        if dictionary_path:
            self._load_dictionary(dictionary_path)

    def _load_dictionary(self, path):
        try:
            data = json.loads(
                Path(path).read_text(encoding='utf-8')
            )

            self.terms = sorted(
                data.get('terms', []),
                key=len,
                reverse=True
            )

        except Exception:
            self.terms = []

    def build(self, text):
        if not text:
            return ''

        text = self._normalize(text)
        text = self._restore_voltage(text)
        text = self._restore_symbols(text)
        text = self._merge_by_dictionary(text)

        return text

    def _normalize(self, text):
        return re.sub(r'\s+', '', text)

    def _restore_voltage(self, text):
        text = text.replace('KV', 'kV')
        text = text.replace('kv', 'kV')
        return text

    def _restore_symbols(self, text):
        return text.replace('＃', '#')

    def _merge_by_dictionary(self, text):
        result = ''
        index = 0

        while index < len(text):
            matched = None

            for term in self.terms:
                term = term.replace(' ', '')

                if text.startswith(term, index):
                    matched = term
                    break

            if matched:
                result += matched
                index += len(matched)
            else:
                result += text[index]
                index += 1

        return result
