# -*- coding: utf-8 -*-

"""OCR layout analysis utilities.

Converts OCR boxes into spatial information.
Text order alone is unreliable for engineering forms.
"""


class LayoutAnalyzer:

    def __init__(self, y_tolerance=20):
        self.y_tolerance = y_tolerance

    def group_lines(self, items):
        """Group OCR boxes by approximate y position."""

        lines = []

        for item in sorted(items, key=lambda x: (x.get('y', 0), x.get('x', 0))):
            current = None

            for line in lines:
                if abs(line['y'] - item.get('y', 0)) <= self.y_tolerance:
                    current = line
                    break

            if current is None:
                current = {
                    'y': item.get('y', 0),
                    'items': []
                }
                lines.append(current)

            current['items'].append(item)

        for line in lines:
            line['items'].sort(key=lambda x: x.get('x', 0))
            line['text'] = ''.join(
                item.get('text', '')
                for item in line['items']
            )

        return lines

    def find_keyword(self, items, keyword):
        for item in items:
            if keyword in item.get('text', ''):
                return item
        return None
