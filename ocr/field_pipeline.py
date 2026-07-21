# -*- coding: utf-8 -*-

"""OCR field processing pipeline.

Combines coordinate reconstruction, project name normalization
and coordinate based field extraction.
"""

from pathlib import Path

from .text_layout import TextLayout
from .project_name_builder import ProjectNameBuilder
from .field_extractor import FieldExtractor


class FieldPipeline:

    def __init__(self, dictionary_path=None):
        self.layout = TextLayout()
        self.name_builder = ProjectNameBuilder(dictionary_path)
        self.extractor = FieldExtractor()

    def process(self, items):
        lines = self.layout.rebuild_lines(items)

        texts = [
            line.get('text', '')
            for line in lines
        ]

        rebuilt = '\n'.join(texts)

        fields = self.extractor.extract(items)

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

    @staticmethod
    def default_dictionary():
        return Path(
            'ocr/dictionaries/power_terms.json'
        )
