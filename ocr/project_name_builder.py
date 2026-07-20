# -*- coding: utf-8 -*-

"""Project name reconstruction for power engineering documents."""

import json
from pathlib import Path


class ProjectNameBuilder:

    def __init__(self, dictionary_path=None):
        self.terms = []

        if dictionary_path:
            self._load_dictionary(dictionary_path)

    def _load_dictionary(self, path):
        try:
            data = json.loads(
                Path(path).read_text(
                    encoding='utf-8'
                )
            )

            self.terms = sorted(
                data.get('terms', []),
                key=len,
                reverse=True
            )

        except Exception:
            self.terms = []

    def build(self, text):
        """Normalize project name text.

        Keeps numbers, symbols and voltage levels.
        """

        if not text:
            return ''

        result = text.replace(
            ' ',
            ''
        )

        result = self._merge_terms(result)

        return result

    def _merge_terms(self, text):
        for term in self.terms:
            if len(term) < 2:
                continue

            compact = term.replace(
                ' ',
                ''
            )

            if compact in text:
                continue

        return text
