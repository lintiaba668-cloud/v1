# -*- coding: utf-8 -*-

"""Engineering report field extraction based on OCR coordinates."""

import logging
import re

logger = logging.getLogger("PowerRename.FieldExtractor")


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
        result = {
            'project_name': self.extract_project_name(items),
            'project_code': self.extract_project_code(items)
        }

        logger.info(
            '[FIELD_EXTRACT] name=%s code=%s',
            result['project_name'],
            result['project_code']
        )

        return result

    def extract_project_code(self, items):
        candidates = []

        for item in items:
            text = item.get('text', '')

            if '工程编号' in text or text == '编号':
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

        ranked = sorted(
            set(candidates),
            key=lambda x: (
                '-' in x,
                any(c.isalpha() for c in x),
                len(x)
            ),
            reverse=True
        )

        return ranked[0]

    def extract_project_name(self, items):
        label = self._find_label(items, '工程名称')

        if not label:
            # 兼容OCR拆字情况：工程 / 名 / 称
            label = self._find_split_label(items)

        if not label:
            logger.warning('[FIELD_EXTRACT] project name label missing')
            return ''

        candidates = []

        for item in items:
            if item is label:
                continue

            text = item.get('text', '').strip()

            if not text or text in IGNORE_FIELDS:
                continue

            same_row = abs(
                item.get('y', 0) - label.get('y', 0)
            ) < 120

            next_row = (
                item.get('y', 0) > label.get('y', 0)
                and item.get('y', 0) - label.get('y', 0) < 400
                and item.get('x', 0) >= label.get('x', 0)
            )

            if same_row or next_row:
                candidates.append(item)

        candidates.sort(
            key=lambda x: (
                x.get('y', 0),
                x.get('x', 0)
            )
        )

        return ''.join(
            item.get('text', '')
            for item in candidates
        )

    def _find_label(self, items, keyword):
        for item in items:
            if keyword in item.get('text', ''):
                return item
        return None

    def _find_split_label(self, items):
        words = []

        for item in items:
            text = item.get('text', '')
            if text in ['工', '程', '名', '称']:
                words.append(item)

        if len(words) < 2:
            return None

        words.sort(key=lambda x: x.get('y', 0))

        merged = dict(words[0])
        merged['text'] = '工程名称'
        return merged

    def _nearby_text(self, items, target):
        result = []

        for item in items:
            if abs(
                item.get('y', 0) - target.get('y', 0)
            ) < 250:
                result.append(item.get('text', ''))

        return ''.join(result)
