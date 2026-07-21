# -*- coding: utf-8 -*-

"""Engineering report field extraction based on OCR coordinates.

Optimized for long power engineering project names that wrap across rows.
"""

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

    CODE_PATTERN = re.compile(
        r'[A-Za-z0-9#\-]{6,}'
    )

    def extract(self, items):
        return {
            'project_name': self.extract_project_name(items),
            'project_code': self.extract_project_code(items)
        }

    def extract_project_code(self, items):
        candidates = []

        for item in items:
            text = item.get('text', '')

            if '工程编号' in text or '编号' in text:
                nearby = self._nearby_text(items, item)
                candidates.extend(
                    self.CODE_PATTERN.findall(nearby)
                )

        if not candidates:
            for item in items:
                candidates.extend(
                    self.CODE_PATTERN.findall(
                        item.get('text', '')
                    )
                )

        return self._select_code(candidates)

    def _select_code(self, candidates):
        if not candidates:
            return ''

        # 优先选择包含数字和符号的工程编号格式
        ranked = sorted(
            candidates,
            key=lambda x: (
                '-' in x,
                any(c.isalpha() for c in x),
                len(x)
            ),
            reverse=True
        )

        return ranked[0]

    def extract_project_name(self, items):
        label = self._find_label(
            items,
            '工程名称'
        )

        if not label:
            return ''

        candidates = []

        for item in items:
            if item is label:
                continue

            text = item.get('text', '').strip()

            if not text:
                continue

            if text in IGNORE_FIELDS:
                continue

            # 同行右侧
            same_row = abs(
                item.get('y', 0) - label.get('y', 0)
            ) < 100

            # 下一行同一单元格区域
            next_row = (
                item.get('y', 0) > label.get('y', 0)
                and item.get('y', 0) - label.get('y', 0) < 300
                and item.get('x', 0) >= label.get('x', 0)
            )

            if same_row or next_row:
                candidates.append(item)

        if not candidates:
            return ''

        candidates.sort(
            key=lambda x: (
                x.get('y', 0),
                x.get('x', 0)
            )
        )

        result = ''.join(
            item.get('text', '')
            for item in candidates
        )

        return result

    def _find_label(self, items, keyword):
        for item in items:
            if keyword in item.get('text', ''):
                return item
        return None

    def _nearby_text(self, items, target):
        result = []

        for item in items:
            if abs(
                item.get('y', 0) - target.get('y', 0)
            ) < 200:
                result.append(
                    item.get('text', '')
                )

        return ''.join(result)
