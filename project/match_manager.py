# -*- coding: utf-8 -*-
"""Project detail matching manager.

Workflow:
OCR result -> imported project library -> ranked candidates ->
auditable automatic/review decision.
"""

from .match_strategy import PowerProjectMatchStrategy


class MatchManager:
    """Coordinate exact/fuzzy-code and power-project-name matching."""

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

        projects = self.project_service.list_projects()
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
                ranked.append((distance, standard, project))

        if not ranked:
            return None

        ranked.sort(key=lambda item: (item[0], item[1]))
        best_distance = ranked[0][0]
        best = [item for item in ranked if item[0] == best_distance]

        # Fuzzy code matching is accepted only when the nearest imported code
        # is unique. Otherwise the result must be resolved by name/review.
        if len(best) != 1:
            return None

        return best[0][2]

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
