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

    CODE_PATTERN = re.compile(r'[A-Za-z0-9#\-]{6,}')

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
        label = self._find_label(items, '工程编号')

        if not label:
            label = self._find_split_label(items, ['工', '程', '编', '号'])

        candidates = []

        if label:
            for item in items:
                text = item.get('text', '').strip()
                if not text:
                    continue

                dx = item.get('x', 0) - label.get('x', 0)
                dy = item.get('y', 0) - label.get('y', 0)

                # 工程编号通常位于标签右侧或下一行
                if (dx > 0 and abs(dy) < 150) or (0 < dy < 300):
                    candidates.extend(self.CODE_PATTERN.findall(text))

        if not candidates:
            for item in items:
                candidates.extend(
                    self.CODE_PATTERN.findall(item.get('text', ''))
                )

        return self._select_code(candidates)

    def _select_code(self, candidates):
        if not candidates:
            return ''

        return sorted(
            set(candidates),
            key=lambda x: (
                '-' in x,
                any(c.isalpha() for c in x),
                len(x)
            ),
            reverse=True
        )[0]

    def extract_project_name(self, items):
        label = self._find_label(items, '工程名称')

        if not label:
            label = self._find_split_label(items, ['工', '程', '名', '称'])

        if not label:
            logger.warning('[FIELD_EXTRACT] project name label missing')
            return ''

        candidates = []
        for item in items:
            text = item.get('text', '').strip()
            if not text or text in IGNORE_FIELDS:
                continue

            if self._name_region_score(label, item) >= 3:
                candidates.append(item)

        candidates.sort(key=lambda x: (x.get('y', 0), x.get('x', 0)))

        return ''.join(item.get('text', '') for item in candidates)

    def _name_region_score(self, label, item):
        score = 0
        dx = item.get('x', 0) - label.get('x', 0)
        dy = item.get('y', 0) - label.get('y', 0)

        if -50 <= dy <= 120 and dx > 0:
            score += 3

        if 0 < dy < 500 and dx > -100:
            score += 2

        if text_after_label(item.get('text', '')):
            score -= 10

        return score

    def _find_label(self, items, keyword):
        for item in items:
            if keyword in item.get('text', ''):
                return item
        return None

    def _find_split_label(self, items, chars):
        words = [
            item for item in items
            if item.get('text', '') in chars
        ]

        if len(words) < 2:
            return None

        words.sort(key=lambda x: x.get('y', 0))
        merged = dict(words[0])
        merged['text'] = ''.join(chars)
        return merged


def text_after_label(text):
    return text in IGNORE_FIELDS
