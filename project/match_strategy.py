# -*- coding: utf-8 -*-
"""Imported power-project matching strategy.

OCR名称允许存在少量错字；Excel项目明细是最终标准数据源。
评分按目标项目实际具备的字段动态归一，避免台区类项目因没有线路号、杆号而
永远达不到自动匹配阈值。
"""

import re
from difflib import SequenceMatcher

from .normalizer import ProjectNormalizer


class PowerProjectMatchStrategy:
    """Score one OCR project name against one imported project name."""

    WEIGHTS = {
        'text_similarity': 60,
        'line': 15,
        'substation': 8,
        'pole': 7,
        'voltage': 5,
        'keywords': 5,
    }

    PENALTIES = {
        'line_conflict': 25,
        'substation_conflict': 15,
        'pole_conflict': 30,
        'voltage_conflict': 20,
        'keywords_conflict': 10,
    }

    POWER_KEYWORDS = (
        '台区', '治理', '开闭所', '公变', '重载', '改造',
        '迁改', '新建', '配套', '业扩', '增容', '线路',
    )

    def __init__(self, normalizer=None):
        self.normalizer = normalizer or ProjectNormalizer()

    def score(self, source, target):
        source_normalized = self.normalizer.normalize(source)
        target_normalized = self.normalizer.normalize(target)

        if not source_normalized or not target_normalized:
            return self._empty_result(source_normalized, target_normalized)

        source_fields = self.extract_fields(source_normalized)
        target_fields = self.extract_fields(target_normalized)

        similarity = SequenceMatcher(
            None,
            source_normalized,
            target_normalized
        ).ratio()

        breakdown = {
            'text_similarity': round(
                similarity * self.WEIGHTS['text_similarity'],
                2
            ),
            'line': self._field_score(
                source_fields['lines'],
                target_fields['lines'],
                self.WEIGHTS['line'],
                self.PENALTIES['line_conflict']
            ),
            'substation': self._field_score(
                source_fields['substations'],
                target_fields['substations'],
                self.WEIGHTS['substation'],
                self.PENALTIES['substation_conflict']
            ),
            'pole': self._field_score(
                source_fields['poles'],
                target_fields['poles'],
                self.WEIGHTS['pole'],
                self.PENALTIES['pole_conflict']
            ),
            'voltage': self._field_score(
                source_fields['voltages'],
                target_fields['voltages'],
                self.WEIGHTS['voltage'],
                self.PENALTIES['voltage_conflict']
            ),
            'keywords': self._field_score(
                source_fields['keywords'],
                target_fields['keywords'],
                self.WEIGHTS['keywords'],
                self.PENALTIES['keywords_conflict']
            ),
        }

        available_weight = self.WEIGHTS['text_similarity']
        field_weights = (
            ('lines', 'line'),
            ('substations', 'substation'),
            ('poles', 'pole'),
            ('voltages', 'voltage'),
            ('keywords', 'keywords'),
        )

        for field_name, weight_name in field_weights:
            if target_fields[field_name]:
                available_weight += self.WEIGHTS[weight_name]

        raw_score = sum(breakdown.values())
        normalized_score = raw_score * 100.0 / float(max(1, available_weight))
        total = max(0.0, min(100.0, normalized_score))

        return {
            'score': round(total, 2),
            'breakdown': breakdown,
            'available_weight': available_weight,
            'source_normalized': source_normalized,
            'target_normalized': target_normalized,
            'source_fields': source_fields,
            'target_fields': target_fields,
        }

    def extract_fields(self, text):
        return {
            'voltages': self._extract_voltages(text),
            'lines': self._extract_named_suffixes(text, '线', 20),
            'substations': self._extract_substations(text),
            'poles': self._extract_poles(text),
            'keywords': self._extract_keywords(text),
        }

    def _extract_voltages(self, text):
        values = re.findall(
            r'(?<!\d)(\d{1,3}(?:\.\d+)?)[kK][vV]',
            text
        )
        return sorted(set(value.lower() + 'kv' for value in values))

    def _extract_named_suffixes(self, text, suffix, max_length):
        pattern = (
            r'[\u4e00-\u9fffA-Za-z0-9#\-]{1,'
            + str(max_length)
            + r'}'
            + re.escape(suffix)
        )
        candidates = re.findall(pattern, text)
        cleaned = []

        for value in candidates:
            value = re.sub(
                r'^.*?\d{1,3}(?:\.\d+)?[kK][vV]',
                '',
                value
            )
            value = value[-max_length:]
            if len(value) > 1:
                cleaned.append(value)

        return sorted(set(cleaned))

    def _extract_substations(self, text):
        candidates = self._extract_named_suffixes(text, '变', 16)
        result = []

        for value in candidates:
            if re.match(r'^#?\d+变$', value):
                continue
            result.append(value)

        return sorted(set(result))

    def _extract_poles(self, text):
        values = re.findall(r'#?0*(\d{1,5})(?:号)?杆', text)
        return sorted(set(str(int(value)) for value in values))

    def _extract_keywords(self, text):
        return sorted(set(
            keyword
            for keyword in self.POWER_KEYWORDS
            if keyword in text
        ))

    def _field_score(self, source_values, target_values, reward, penalty):
        source_set = set(source_values)
        target_set = set(target_values)

        if not target_set:
            return 0

        if not source_set:
            return 0

        if source_set & target_set:
            return reward

        return -penalty

    def _empty_result(self, source_normalized, target_normalized):
        return {
            'score': 0.0,
            'breakdown': {
                'text_similarity': 0.0,
                'line': 0,
                'substation': 0,
                'pole': 0,
                'voltage': 0,
                'keywords': 0,
            },
            'available_weight': self.WEIGHTS['text_similarity'],
            'source_normalized': source_normalized,
            'target_normalized': target_normalized,
            'source_fields': self.extract_fields(source_normalized),
            'target_fields': self.extract_fields(target_normalized),
        }
