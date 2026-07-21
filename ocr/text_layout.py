# -*- coding: utf-8 -*-

"""OCR coordinate layout reconstruction."""

import logging

logger = logging.getLogger("PowerRename.TextLayout")


class TextLayout:

    def __init__(self, y_threshold=25, x_gap_threshold=40):
        self.y_threshold = y_threshold
        self.x_gap_threshold = x_gap_threshold

    def rebuild_lines(self, items):
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
                if abs(line['y'] - item.get('y', 0)) <= self.y_threshold:
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

        result = self.merge_vertical_labels(result)

        return result

    def merge_items(self, items):
        result = ''
        previous = None

        for item in items:
            text = item.get('text', '')
            if not text:
                continue

            if previous:
                gap = item.get('x', 0) - (
                    previous.get('x', 0) + previous.get('w', 0)
                )
                if gap > self.x_gap_threshold:
                    result += ''

            result += text
            previous = item

        return result

    def merge_vertical_labels(self, lines):
        """Recover labels split into vertical single characters."""

        merged = []
        index = 0

        while index < len(lines):
            current = lines[index]

            texts = [
                current.get('text', '')
            ]

            if index + 3 < len(lines):
                texts = [
                    lines[index+i].get('text', '')
                    for i in range(4)
                ]

                if ''.join(texts) in ['工程名称', '工程编号']:
                    new_line = dict(current)
                    new_line['text'] = ''.join(texts)
                    merged.append(new_line)
                    index += 4
                    continue

            merged.append(current)
            index += 1

        return merged

    def rebuild_text(self, items):
        lines = self.rebuild_lines(items)
        return '\n'.join(
            line['text']
            for line in lines
        )
