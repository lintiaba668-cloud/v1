# -*- coding: utf-8 -*-
"""Project detail matching manager.

Workflow:
OCR result -> imported project library -> ranked candidates ->
auditable automatic/review decision.
"""

import re

from .match_strategy import PowerProjectMatchStrategy


class MatchManager:
    """Coordinate exact/fuzzy-code and power-project-name matching."""

    OCR_CONFUSABLE_GROUPS = (
        frozenset('1IL'),
        frozenset('0ODQ'),
        frozenset('0C'),
        frozenset('2Z'),
    )

    def __init__(
        self,
        project_service=None,
        correction=None,
        strategy=None,
        matched_threshold=76,
        uncertain_threshold=58,
        min_margin=8,
        candidate_limit=3
    ):
        self.project_service = project_service
        self.correction = correction
        self.strategy = strategy or PowerProjectMatchStrategy()
        self.matched_threshold = float(matched_threshold)
        self.uncertain_threshold = float(uncertain_threshold)
        self.min_margin = float(min_margin)
        self.candidate_limit = max(1, int(candidate_limit))

    def normalize_text(self, text):
        if not text:
            return ''

        value = str(text).strip()

        if self.correction:
            value = self.correction.correct(value)

        return value

    def match_project(self, ocr_text='', project_code=''):
        """Match one OCR result against the imported project library."""
        if not self.project_service:
            return self._empty_result('project_service_unavailable')

        code = self._normalize_code(project_code)

        if code:
            exact = self.project_service.find_by_code(code)
            if exact:
                return self._code_result(
                    exact,
                    source='project_code',
                    reason='exact_project_code',
                    score=100.0,
                )

            sequence = self._find_unique_sequence_code(code)
            if sequence:
                return self._code_result(
                    sequence,
                    source='project_code_sequence',
                    reason='sequence_suffix_equivalent',
                    score=99.0,
                )

            confusable = self._find_unique_ocr_confusable_code(code)
            if confusable:
                return self._code_result(
                    confusable,
                    source='project_code_ocr_confusable',
                    reason='unique_ocr_confusable_project_code',
                    score=99.0,
                )

            degraded = self._find_unique_degraded_ocr_code(code)
            if degraded:
                return self._code_result(
                    degraded,
                    source='project_code_ocr_degraded',
                    reason='unique_degraded_ocr_project_code',
                    score=97.0,
                )

            fuzzy = self._find_unique_fuzzy_code(code)
            if fuzzy:
                return self._code_result(
                    fuzzy,
                    source='project_code_fuzzy',
                    reason='unique_one_edit_project_code',
                    score=98.0,
                )

        text = self.normalize_text(ocr_text)
        if not text:
            return self._empty_result('empty_ocr_project_name')

        projects = self._coalesce_equivalent_projects(
            self.project_service.list_projects()
        )
        if not projects:
            return self._empty_result('empty_project_library')

        candidates = []

        for project in projects:
            project_name = project.get('project_name', '')
            detail = self.strategy.score(text, project_name)

            candidates.append({
                'project_code': project.get('project_code', '') or '',
                'project_name': project_name,
                'score': detail['score'],
                'breakdown': detail['breakdown'],
                'source_fields': detail['source_fields'],
                'target_fields': detail['target_fields'],
            })

        candidates.sort(
            key=lambda item: (
                item['score'],
                bool(item['project_code']),
                item['project_name']
            ),
            reverse=True
        )

        top = candidates[0]
        second_score = candidates[1]['score'] if len(candidates) > 1 else 0.0
        margin = round(top['score'] - second_score, 2)

        status, reason = self._decide_status(
            top['score'],
            margin,
            len(candidates)
        )
        auto_accepted = status == 'matched'

        return {
            'status': status,
            'auto_accepted': auto_accepted,
            'match_source': 'project_name',
            'reason': reason,
            'score': top['score'],
            'margin': margin,
            'project_code': top['project_code'] if auto_accepted else '',
            'project_name': top['project_name'] if auto_accepted else '',
            'suggested_project_code': top['project_code'],
            'suggested_project_name': top['project_name'],
            'candidates': candidates[:self.candidate_limit],
        }

    def batch_match(self, ocr_results):
        results = []

        for index, item in enumerate(ocr_results):
            if isinstance(item, dict):
                project_name = (
                    item.get('project_name')
                    or item.get('name')
                    or item.get('text')
                    or ''
                )
                project_code = item.get('project_code', '')
            else:
                project_name = str(item or '')
                project_code = ''

            matched = self.match_project(
                ocr_text=project_name,
                project_code=project_code
            )
            matched['source_index'] = index
            matched['source_project_name'] = project_name
            matched['source_project_code'] = project_code
            results.append(matched)

        return results

    def _find_unique_sequence_code(self, code):
        """Match the two numbering forms used for the same project sequence.

        A printed report may use ``<12-digit base>-N``, while the imported
        project list stores ``<12-digit base><N+1 as two digits>``:
        ``-1 == 02``, ``-2 == 03``, ..., ``-5 == 06``.

        The rule is intentionally limited to a 12-character alphanumeric base
        so normal shorter codes are never split as sequence numbers. Lettered
        bases such as ``18132024015D-15`` are valid.
        """
        aliases = self._sequence_code_aliases(code)
        matches = {}

        for alias in aliases:
            project = self.project_service.find_by_code(alias)
            if not project:
                continue
            standard = self._normalize_code(project.get('project_code', ''))
            if standard:
                matches[standard] = project

        if len(matches) != 1:
            return None

        return list(matches.values())[0]

    def _find_unique_ocr_confusable_code(self, code):
        """Resolve OCR glyph substitutions only when one project is possible.

        Printed engineering numbers mix letters and digits. Tesseract
        commonly swaps L/I/1, D/O/Q/0, C/0, and Z/2 on small or slanted
        cells. This path deliberately accepts substitutions only (never
        insertion or deletion), and only when the imported project library
        has one unique confusable match.
        """
        matches = {}

        for project in self.project_service.list_projects():
            standard = self._normalize_code(project.get('project_code', ''))
            if (
                len(code) < 8
                or len(code) != len(standard)
                or not self._only_ocr_confusable_differences(code, standard)
            ):
                continue

            matches[standard] = project

        if len(matches) != 1:
            return None

        return list(matches.values())[0]

    def _find_unique_degraded_ocr_code(self, code):
        """Recover a clipped prefix plus a small number of OCR glyph errors.

        Slanted completion-report cells can lose the leading ``B``/``C`` and
        simultaneously read ``Z`` as ``2`` or ``7``. This compound damage is
        outside the one-edit and same-length confusable paths. It is accepted
        only for long codes and only when one imported project remains.
        """
        if len(code) < 10:
            return None

        matches = {}

        for project in self.project_service.list_projects():
            standard = self._normalize_code(project.get('project_code', ''))
            leading_loss = len(standard) - len(code)

            if leading_loss not in (1, 2):
                continue

            aligned = standard[leading_loss:]
            if len(aligned) != len(code):
                continue

            confusable_count = 0
            other_count = 0

            for source_char, target_char in zip(code, aligned):
                if source_char == target_char:
                    continue

                if any(
                    source_char in group and target_char in group
                    for group in self.OCR_CONFUSABLE_GROUPS
                ):
                    confusable_count += 1
                else:
                    other_count += 1

            if (
                confusable_count >= 1
                and confusable_count + other_count <= 3
                and other_count <= 1
            ):
                matches[standard] = project

        if len(matches) != 1:
            return None

        return list(matches.values())[0]

    @classmethod
    def _only_ocr_confusable_differences(cls, source, target):
        difference_count = 0

        for source_char, target_char in zip(source, target):
            if source_char == target_char:
                continue

            difference_count += 1
            if not any(
                source_char in group and target_char in group
                for group in cls.OCR_CONFUSABLE_GROUPS
            ):
                return False

        return difference_count > 0

    @staticmethod
    def _sequence_code_aliases(value):
        code = ''.join(str(value or '').split()).upper()
        aliases = set()

        printed = re.match(r'^([A-Z0-9]{12})-(\d{1,2})$', code)
        if printed:
            sequence = int(printed.group(2))
            if 1 <= sequence <= 98:
                aliases.add(
                    printed.group(1) + '{:02d}'.format(sequence + 1)
                )

        imported = re.match(r'^([A-Z0-9]{12})(\d{2})$', code)
        if imported:
            sequence = int(imported.group(2))
            if 2 <= sequence <= 99:
                aliases.add(
                    imported.group(1) + '-' + str(sequence - 1)
                )

        return aliases

    def _coalesce_equivalent_projects(self, projects):
        """Treat duplicate old/new sequence rows as one name candidate.

        Imported workbooks can contain both ``base-N`` and ``baseNN`` rows
        for the same project name. They are the same business identifier, so
        they must not create an artificial zero-point margin during name
        matching. Prefer the newer two-digit suffix in the returned record.
        """
        grouped = {}

        for project in projects:
            name = self.normalize_text(project.get('project_name', ''))
            name_key = re.sub(r'\s+', '', name).lower()
            code = self._normalize_code(project.get('project_code', ''))
            canonical = self._canonical_sequence_code(code)
            key = (name_key, canonical)
            existing = grouped.get(key)

            if existing is None:
                grouped[key] = project
                continue

            existing_code = self._normalize_code(
                existing.get('project_code', '')
            )
            if code == canonical and existing_code != canonical:
                grouped[key] = project

        return list(grouped.values())

    @staticmethod
    def _canonical_sequence_code(value):
        code = ''.join(str(value or '').split()).upper()
        printed = re.match(r'^([A-Z0-9]{12})-(\d{1,2})$', code)

        if not printed:
            return code

        sequence = int(printed.group(2))
        if not 1 <= sequence <= 98:
            return code

        return printed.group(1) + '{:02d}'.format(sequence + 1)

    def _find_unique_fuzzy_code(self, code):
        projects = self.project_service.list_projects()
        ranked = []

        for project in projects:
            standard = self._normalize_code(project.get('project_code', ''))
            if not standard:
                continue

            # Short codes are too ambiguous for automatic fuzzy correction.
            if min(len(code), len(standard)) < 8:
                continue

            distance = self._levenshtein(code, standard, stop_after=1)
            if distance <= 1:
                ranked.append((0, distance, standard, project))
                continue

            # Completion-report OCR can lose one or two leading characters
            # while keeping the long, distinctive remainder intact.  Accept
            # this only through the same uniqueness check used below.
            prefix_loss = len(standard) - len(code)
            if (
                len(code) >= 10
                and prefix_loss in (1, 2)
                and standard.endswith(code)
            ):
                ranked.append((1, prefix_loss, standard, project))

        if not ranked:
            return None

        ranked.sort(key=lambda item: (item[0], item[1], item[2]))
        best_rank = ranked[0][:2]
        best = [item for item in ranked if item[:2] == best_rank]

        # Fuzzy code matching is accepted only when the nearest imported code
        # is unique. Otherwise the result must be resolved by name/review.
        if len(best) != 1:
            return None

        return best[0][3]

    @staticmethod
    def _levenshtein(source, target, stop_after=None):
        if source == target:
            return 0

        if stop_after is not None and abs(len(source) - len(target)) > stop_after:
            return stop_after + 1

        previous = list(range(len(target) + 1))

        for source_index, source_char in enumerate(source, 1):
            current = [source_index]
            row_minimum = current[0]

            for target_index, target_char in enumerate(target, 1):
                value = min(
                    current[-1] + 1,
                    previous[target_index] + 1,
                    previous[target_index - 1] + (
                        0 if source_char == target_char else 1
                    ),
                )
                current.append(value)
                row_minimum = min(row_minimum, value)

            if stop_after is not None and row_minimum > stop_after:
                return stop_after + 1

            previous = current

        return previous[-1]

    @staticmethod
    def _code_result(project, source, reason, score):
        return {
            'status': 'matched',
            'auto_accepted': True,
            'match_source': source,
            'reason': reason,
            'score': float(score),
            'margin': 100.0,
            'project_code': project.get('project_code', ''),
            'project_name': project.get('project_name', ''),
            'suggested_project_code': project.get('project_code', ''),
            'suggested_project_name': project.get('project_name', ''),
            'candidates': [],
        }

    def _decide_status(self, score, margin, candidate_count):
        if score >= self.matched_threshold:
            if candidate_count == 1 or margin >= self.min_margin:
                return 'matched', 'score_and_margin_passed'
            return 'uncertain', 'candidate_scores_too_close'

        if score >= self.uncertain_threshold:
            return 'uncertain', 'score_requires_manual_review'

        return 'unmatched', 'score_below_threshold'

    def _normalize_code(self, value):
        if value is None:
            return ''
        return ''.join(str(value).split()).upper()

    def _empty_result(self, reason):
        return {
            'status': 'unmatched',
            'auto_accepted': False,
            'match_source': 'none',
            'reason': reason,
            'score': 0.0,
            'margin': 0.0,
            'project_code': '',
            'project_name': '',
            'suggested_project_code': '',
            'suggested_project_name': '',
            'candidates': [],
        }
