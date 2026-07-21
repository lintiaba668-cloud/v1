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

    CODE_PATTERN = re.compile(
        r'[A-Za-z0-9#\-]{6,}'
    )

    def extract(self, items):
        return {
            'project_name': self.extract_project_name(items),
            'project_code': self.extract_project_code(items)
        }

    def extract_project_code(self, items):
        for item in items:
            text = item.get('text', '')

            if '工程编号' in text or '编号' in text:
                nearby = self._nearby_text(items, item)
                result = self.CODE_PATTERN.search(nearby)

                if result:
                    return result.group(0)

        for item in items:
            result = self.CODE_PATTERN.search(
                item.get('text', '')
            )
            if result:
                return result.group(0)

        return ''

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

            # 优先读取标签右侧区域
            same_row = abs(
                item.get('y', 0) - label.get('y', 0)
            ) < 80

            right_side = item.get('x', 0) > label.get('x', 0)

            if same_row and right_side:
                text = item.get('text', '').strip()
                if text and text not in IGNORE_FIELDS:
                    candidates.append(item)

        if candidates:
            return ''.join(
                item.get('text', '')
                for item in sorted(
                    candidates,
                    key=lambda x: x.get('x', 0)
                )
            )

        return ''

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
