# -*- coding: utf-8 -*-

"""OCR field processing pipeline.

Combines coordinate reconstruction, OCR correction,
project name normalization and field extraction.
"""

from pathlib import Path

from .text_layout import TextLayout
from .project_name_builder import ProjectNameBuilder
from .field_extractor import FieldExtractor
from .dictionary import OCRDictionary


class FieldPipeline:

    def __init__(self, dictionary_path=None, correction_path=None):
        self.layout = TextLayout()
        self.name_builder = ProjectNameBuilder(dictionary_path)
        self.extractor = FieldExtractor()
        self.dictionary = OCRDictionary(correction_path)

    def process(self, items):
        lines = self.layout.rebuild_lines(items)

        corrected_items = self._correct_items(items)

        corrected_lines = self.layout.rebuild_lines(
            corrected_items
        )

        texts = [
            line.get('text', '')
            for line in corrected_lines
        ]

        rebuilt = '\n'.join(texts)

        fields = self.extractor.extract(
            corrected_items
        )

        if fields.get('project_name'):
            fields['project_name'] = self.name_builder.build(
                fields['project_name']
            )

        return {
            'layout_text': rebuilt,
            'fields': fields,
            'project_name_candidates': [
                self.name_builder.build(text)
                for text in texts
                if text
            ]
        }

    def _correct_items(self, items):
        result = []

        for item in items:
            new_item = dict(item)
            new_item['text'] = self.dictionary.correct(
                item.get('text', '')
            )
            result.append(new_item)

        return result

    @staticmethod
    def default_dictionary():
        return Path(
            'ocr/dictionaries/power_terms.json'
        )
