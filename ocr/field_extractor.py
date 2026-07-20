# -*- coding: utf-8 -*-

"""Engineering report field extraction based on OCR coordinates."""

import re


IGNORE_FIELDS = [
    '建设单位',
    '设计单位',
    '施工单位',
    '监理单位',
    '工程编号',
    '主要工程内容'
]


class FieldExtractor:

    def extract_project_code(self, items):
        for item in items:
            text = item.get('text', '')
            if '工程编号' in text or '编号' in text:
                nearby = self._nearby_text(items, item)
                result = re.search(
                    r'[A-Z0-9\-]{6,}',
                    nearby
                )
                if result:
                    return result.group(0)

        return ''

    def extract_project_name(self, items):
        label = self._find_label(items, '工程名称')

        if not label:
            return ''

        candidates = []

        for item in items:
            if item is label:
                continue

            if item.get('y', 0) < label.get('y', 0):
                continue

            if item.get('y', 0) > label.get('y', 0) + 500:
                continue

            text = item.get('text', '').strip()

            if text and text not in IGNORE_FIELDS:
                candidates.append(text)

        return ''.join(candidates)

    def _find_label(self, items, keyword):
        for item in items:
            if keyword in item.get('text', ''):
                return item
        return None

    def _nearby_text(self, items, target):
        result = []
        for item in items:
            if abs(item.get('y', 0) - target.get('y', 0)) < 200:
                result.append(item.get('text', ''))
        return ''.join(result)
