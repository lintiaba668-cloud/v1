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
        'facility': 15,
    }

    PENALTIES = {
        'line_conflict': 25,
        'substation_conflict': 15,
        'pole_conflict': 32,
        'voltage_conflict': 20,
        'keywords_conflict': 10,
        'facility_conflict': 15,
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

        similarity = self._text_similarity(
            source_normalized,
            target_normalized,
        )

        breakdown = {
            'text_similarity': round(
                similarity * self.WEIGHTS['text_similarity'],
                2
            ),
            'line': self._field_score(
                source_fields['lines'],
                target_fields['lines'],
                self.WEIGHTS['line'],
                self.PENALTIES['line_conflict'],
                fuzzy_threshold=0.68,
            ),
            'substation': self._field_score(
                source_fields['substations'],
                target_fields['substations'],
                self.WEIGHTS['substation'],
                self.PENALTIES['substation_conflict'],
                fuzzy_threshold=0.7,
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
            'facility': self._field_score(
                source_fields['facilities'],
                target_fields['facilities'],
                self.WEIGHTS['facility'],
                self.PENALTIES['facility_conflict'],
                fuzzy_threshold=0.8,
            ),
        }

        available_weight = self.WEIGHTS['text_similarity']
        field_weights = (
            ('lines', 'line'),
            ('substations', 'substation'),
            ('poles', 'pole'),
            ('voltages', 'voltage'),
            ('keywords', 'keywords'),
            ('facilities', 'facility'),
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
            'facilities': self._extract_facilities(text),
        }

    def _extract_voltages(self, text):
        values = re.findall(
            r'(?<!\d)(\d{1,3}(?:\.\d+)?)[kK][vV]',
            text
        )
        return sorted(set(value.lower() + 'kv' for value in values))

    def _extract_named_suffixes(self, text, suffix, max_length):
        quantifier = (
            r'{1,' + str(max_length) + r'}?'
            if suffix == '线'
            else r'{1,' + str(max_length) + r'}'
        )
        pattern = (
            r'[\u4e00-\u9fffA-Za-z0-9#\-]'
            + quantifier
            + re.escape(suffix)
        )
        candidates = re.findall(pattern, text)
        cleaned = []

        for value in candidates:
            value = re.sub(
                r'^.*\d{1,3}(?:\.\d+)?[kK][vV]',
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
            if '线' in value:
                continue
            if value.endswith(('公变', '配变', '箱式变')):
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

    def _extract_facilities(self, text):
        """Return suffix variants for named distribution facilities.

        OCR often corrupts the city prefix while preserving a distinctive
        facility such as "坑边开闭所".  Suffix variants retain that stable
        anchor without treating the generic word "开闭所" alone as a match.
        """
        facilities = set()
        suffixes = ('开闭所', '环网柜', '配电室', '箱式变', '公变')

        for suffix in suffixes:
            pattern = (
                r'([\u4e00-\u9fffA-Za-z0-9#\-]{2,12})'
                + re.escape(suffix)
            )
            for prefix in re.findall(pattern, text):
                for length in range(2, min(6, len(prefix)) + 1):
                    facilities.add(prefix[-length:] + suffix)

        return sorted(facilities)

    def _text_similarity(self, source, target):
        source_comparable = self._comparison_text(source)
        target_comparable = self._comparison_text(target)

        if not source_comparable or not target_comparable:
            return 0.0

        return SequenceMatcher(
            None,
            source_comparable,
            target_comparable,
        ).ratio()

    @staticmethod
    def _comparison_text(value):
        # Preserve domain notation while removing long Latin OCR garbage.
        text = re.sub(
            r'(?i)(\d{1,3})k[vY]',
            r'\1千伏',
            str(value),
        )
        text = re.sub(r'[A-Za-z]{2,}', '', text)
        return re.sub(
            r'[^\u4e00-\u9fff0-9#ⅠⅡⅢⅣⅤ\-]',
            '',
            text,
        )

    def _field_score(
        self,
        source_values,
        target_values,
        reward,
        penalty,
        fuzzy_threshold=None,
    ):
        source_set = set(source_values)
        target_set = set(target_values)

        if not target_set:
            return 0

        if not source_set:
            return 0

        if source_set & target_set:
            return reward

        if fuzzy_threshold is not None:
            best_similarity = max(
                SequenceMatcher(None, source, target).ratio()
                for source in source_set
                for target in target_set
            )
            if best_similarity >= fuzzy_threshold:
                return round(reward * best_similarity, 2)

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
                'facility': 0,
            },
            'available_weight': self.WEIGHTS['text_similarity'],
            'source_normalized': source_normalized,
            'target_normalized': target_normalized,
            'source_fields': self.extract_fields(source_normalized),
            'target_fields': self.extract_fields(target_normalized),
        }
