# -*- coding: utf-8 -*-
"""
OCR correction dictionary learning module.

Store confirmed OCR corrections for future recognition.
"""

import json
from pathlib import Path


class CorrectionLearning:

    def __init__(self, dictionary_path='ocr/dictionary.json'):
        self.path = Path(dictionary_path)
        self.rules = self._load()

    def _load(self):
        if not self.path.exists():
            return {}

        with open(self.path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def add(self, wrong, correct):
        if not wrong or not correct:
            return False

        self.rules[wrong] = correct
        self._save()
        return True

    def _save(self):
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(self.path, 'w', encoding='utf-8') as file:
            json.dump(
                self.rules,
                file,
                ensure_ascii=False,
                indent=2
            )

    def all_rules(self):
        return self.rules
