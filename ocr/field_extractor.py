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
        candidates = []

        for item in items:
            text = item.get('text', '')
            if '工程编号' in text or text == '编号':
                candidates.extend(
                    self.CODE_PATTERN.findall(
                        self._nearby_text(items, item)
                    )
                )

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
            label = self._find_split_label(items)

        if not label:
            logger.warning('[FIELD_EXTRACT] project name label missing')
            return ''

        candidates = []

        for item in items:
            text = item.get('text', '').strip()

            if not text or text in IGNORE_FIELDS:
                continue

            score = self._name_region_score(label, item)

            if score >= 3:
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

    def _name_region_score(self, label, item):
        score = 0

        dx = item.get('x', 0) - label.get('x', 0)
        dy = item.get('y', 0) - label.get('y', 0)

        # 同行右侧优先
        if dy >= -50 and dy <= 120 and dx > 0:
            score += 3

        # 下一行同单元格
        if 0 < dy < 500 and dx > -100:
            score += 2

        # 过滤明显后续字段
        if text_after_label(item.get('text', '')):
            score -= 10

        return score

    def _find_label(self, items, keyword):
        for item in items:
            if keyword in item.get('text', ''):
                return item
        return None

    def _find_split_label(self, items):
        words = [
            item for item in items
            if item.get('text', '') in ['工', '程', '名', '称']
        ]

        if len(words) < 2:
            return None

        words.sort(key=lambda x: x.get('y', 0))
        merged = dict(words[0])
        merged['text'] = '工程名称'
        return merged

    def _nearby_text(self, items, target):
        return ''.join(
            item.get('text', '')
            for item in items
            if abs(item.get('y', 0)-target.get('y', 0)) < 250
        )


def text_after_label(text):
    return text in IGNORE_FIELDS
