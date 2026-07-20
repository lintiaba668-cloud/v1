# -*- coding: utf-8 -*-

"""OCR coordinate layout reconstruction.

Rebuilds text order from TSV boxes instead of relying only on OCR raw text.
Designed for engineering reports where Chinese characters may be split.
"""


class TextLayout:

    def __init__(self, y_threshold=25, x_gap_threshold=40):
        self.y_threshold = y_threshold
        self.x_gap_threshold = x_gap_threshold

    def rebuild_lines(self, items):
        """Group OCR boxes into visual lines."""

        lines = []

        ordered = sorted(
            items,
            key=lambda x: (
                x.get('y', 0),
                x.get('x', 0)
            )
        )

        for item in ordered:
            matched = None

            for line in lines:
                if abs(
                    line['y'] - item.get('y', 0)
                ) <= self.y_threshold:
                    matched = line
                    break

            if matched is None:
                matched = {
                    'y': item.get('y', 0),
                    'items': []
                }
                lines.append(matched)

            matched['items'].append(item)

        result = []

        for line in lines:
            chars = sorted(
                line['items'],
                key=lambda x: x.get('x', 0)
            )

            result.append({
                'y': line['y'],
                'items': chars,
                'text': self.merge_items(chars)
            })

        return result

    def merge_items(self, items):
        """Merge OCR boxes while preserving engineering symbols."""

        result = ''

        previous = None

        for item in items:
            text = item.get('text', '')

            if not text:
                continue

            if previous:
                gap = item.get('x', 0) - (
                    previous.get('x', 0)
                    + previous.get('w', 0)
                )

                if gap > self.x_gap_threshold:
                    result += ''

            result += text
            previous = item

        return result

    def rebuild_text(self, items):
        lines = self.rebuild_lines(items)

        return '\n'.join(
            line['text']
            for line in lines
        )
