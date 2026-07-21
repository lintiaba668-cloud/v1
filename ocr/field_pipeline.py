# -*- coding: utf-8 -*-

"""OCR field processing pipeline.

Combines coordinate reconstruction and power engineering
project name normalization.
"""

from pathlib import Path

from .text_layout import TextLayout
from .project_name_builder import ProjectNameBuilder


class FieldPipeline:

    def __init__(self, dictionary_path=None):
        self.layout = TextLayout()
        self.name_builder = ProjectNameBuilder(
            dictionary_path
        )

    def process(self, items):
        """Process OCR TSV items.

        Returns reconstructed text and candidate lines.
        """

        lines = self.layout.rebuild_lines(items)

        texts = [
            line.get('text', '')
            for line in lines
        ]

        rebuilt = '\n'.join(texts)

        return {
            'layout_text': rebuilt,
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
