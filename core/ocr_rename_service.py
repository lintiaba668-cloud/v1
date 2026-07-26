"""OCR recognition to standard project matching and file output service."""

from pathlib import Path
import re
import unicodedata

from ocr.pipeline_ocr import OCRPipeline
from core.rename import rename_file
from project.project_service import ProjectService


class OCRRenameService:
    def __init__(
        self,
        output_dir,
        project_service=None,
        output_lock=None,
    ):
        self.output_dir = Path(output_dir)
        self.pipeline = OCRPipeline()
        self.project_service = project_service or ProjectService()
        self.output_lock = output_lock

    def process(self, image, recognition_mode='deep'):
        image_path = Path(image)
        filename_hint = self._filename_project_hint(image_path)
        result = self.pipeline.process(
            image_path,
            recognition_mode=recognition_mode,
        )

        if not result.get('valid'):
            if filename_hint:
                return self._rename_from_filename_hint(
                    image_path,
                    filename_hint,
                    result,
                )
            return {
                'status': 'failed',
                'source': str(image_path),
                'target': '',
                'error': result.get('error', 'OCR结果无有效目标字段'),
                'ocr_project_name': '',
                'ocr_project_code': '',
                'report_type': '',
                'matched': False,
            }

        data = result.get('data', {})
        report_type = data.get('report_type', '')
        name_candidates = self._deduplicate(
            data.get('project_name_candidates', [])
            or [data.get('project_name', '')]
        )
        code_candidates = self._deduplicate(
            data.get('project_code_candidates', [])
            or [data.get('project_code', '')]
        )

        match = self._match_candidates(name_candidates, code_candidates)
        selected_name = match.pop('_selected_ocr_name', '')
        selected_code = match.pop('_selected_ocr_code', '')

        if not match.get('auto_accepted'):
            if (
                filename_hint
                and (
                    not report_type
                    or report_type == filename_hint['report_type']
                )
            ):
                original = dict(result)
                original['ocr_project_name'] = (
                    selected_name
                    or (name_candidates[0] if name_candidates else '')
                )
                original['ocr_project_code'] = (
                    selected_code
                    or (code_candidates[0] if code_candidates else '')
                )
                original['ocr_project_name_candidates'] = name_candidates
                original['ocr_project_code_candidates'] = code_candidates
                return self._rename_from_filename_hint(
                    image_path,
                    filename_hint,
                    original,
                )
            match_status = match.get('status', 'unmatched')
            return {
                'status': (
                    'review_required'
                    if match_status == 'uncertain'
                    else 'unmatched'
                ),
                'source': str(image_path),
                'target': '',
                'ocr_project_name': selected_name or (
                    name_candidates[0] if name_candidates else ''
                ),
                'ocr_project_code': selected_code or (
                    code_candidates[0] if code_candidates else ''
                ),
                'ocr_project_name_candidates': name_candidates,
                'ocr_project_code_candidates': code_candidates,
                'report_type': report_type,
                'project_name': '',
                'project_code': '',
                'suggested_project_name': match.get(
                    'suggested_project_name', ''
                ),
                'suggested_project_code': match.get(
                    'suggested_project_code', ''
                ),
                'matched': False,
                'match_source': match.get('match_source', 'none'),
                'match_score': match.get('score', 0.0),
                'match_margin': match.get('margin', 0.0),
                'match_reason': match.get('reason', ''),
                'candidates': match.get('candidates', []),
            }

        project_name = match.get('project_name', '')
        project_code = match.get('project_code', '')

        if not project_name:
            return {
                'status': 'failed',
                'source': str(image_path),
                'target': '',
                'error': '匹配结果缺少标准工程名称',
                'ocr_project_name': selected_name,
                'ocr_project_code': selected_code,
                'report_type': report_type,
                'matched': False,
            }

        if not project_code:
            return {
                'status': 'failed',
                'source': str(image_path),
                'target': '',
                'error': '匹配到的工程明细缺少工程编号，无法按命名规则输出',
                'ocr_project_name': selected_name,
                'ocr_project_code': selected_code,
                'report_type': report_type,
                'project_name': project_name,
                'project_code': '',
                'matched': True,
            }

        original = dict(result)
        original['ocr_project_name'] = selected_name
        original['ocr_project_code'] = selected_code
        original['ocr_project_name_candidates'] = name_candidates
        original['ocr_project_code_candidates'] = code_candidates

        return self._rename_with_project(
            image_path=image_path,
            project_name=project_name,
            project_code=project_code,
            report_type=report_type,
            original=original,
            match=match,
            manual_confirmed=False
        )

    def _filename_project_hint(self, image_path):
        """Read only a strict, previously generated filename convention."""
        stem = str(Path(image_path).stem or '')
        report_type = 'finish'
        if stem.endswith('_开工'):
            report_type = 'start'
            stem = stem[:-3]

        if '_' not in stem:
            return None

        name_hint, code_hint = stem.rsplit('_', 1)
        code_hint = ''.join(code_hint.split()).upper()
        if not re.match(r'^[A-Z0-9#-]{8,24}$', code_hint):
            return None

        finder = getattr(self.project_service, 'find_by_code', None)
        if not callable(finder):
            return None

        project = finder(code_hint)
        if not project:
            return None

        def normalize_name(value):
            value = unicodedata.normalize('NFKC', str(value or ''))
            return re.sub(r'\s+', '', value).casefold()

        if (
            len(normalize_name(name_hint)) < 8
            or normalize_name(name_hint)
            != normalize_name(project.get('project_name', ''))
        ):
            return None

        return {
            'report_type': report_type,
            'project_name': project.get('project_name', ''),
            'project_code': project.get('project_code', ''),
        }

    def _rename_from_filename_hint(self, image_path, hint, original):
        return self._rename_with_project(
            image_path=image_path,
            project_name=hint['project_name'],
            project_code=hint['project_code'],
            report_type=hint['report_type'],
            original=original,
            match={
                'match_source': 'verified_filename',
                'score': 100.0,
                'margin': 100.0,
                'reason': 'exact_filename_name_and_code_in_project_library',
                'candidates': [],
            },
            manual_confirmed=False,
        )

    def _match_candidates(self, name_candidates, code_candidates):
        attempts = []
        primary_name = name_candidates[0] if name_candidates else ''

        # Code candidates are evaluated first. Exact, business-sequence, or
        # unique one-edit matching is safer than accepting raw OCR text.
        for code in code_candidates:
            matched = self.project_service.match_project(
                project_name=primary_name,
                project_code=code,
            )
            matched['_selected_ocr_name'] = primary_name
            matched['_selected_ocr_code'] = code
            attempts.append(matched)

        # Each field OCR variant is matched independently. This allows one
        # crop/PSM variant to fail while another still resolves the Excel row.
        for name in name_candidates:
            matched = self.project_service.match_project(
                project_name=name,
                project_code='',
            )
            matched['_selected_ocr_name'] = name
            matched['_selected_ocr_code'] = ''
            attempts.append(matched)

        if not attempts:
            return {
                'status': 'unmatched',
                'auto_accepted': False,
                'match_source': 'none',
                'reason': 'empty_ocr_candidates',
                'score': 0.0,
                'margin': 0.0,
                'project_code': '',
                'project_name': '',
                'suggested_project_code': '',
                'suggested_project_name': '',
                'candidates': [],
                '_selected_ocr_name': '',
                '_selected_ocr_code': '',
            }

        accepted_codes = {}
        for attempt in attempts:
            if (
                attempt.get('auto_accepted')
                and str(attempt.get('match_source', '')).startswith(
                    'project_code'
                )
                and attempt.get('project_code')
            ):
                accepted_codes.setdefault(
                    attempt['project_code'],
                    attempt,
                )

        if len(accepted_codes) > 1:
            conflicts = list(accepted_codes.values())
            conflicts.sort(key=self._match_rank, reverse=True)
            best = conflicts[0]
            return {
                'status': 'uncertain',
                'auto_accepted': False,
                'match_source': 'project_code_conflict',
                'reason': 'conflicting_code_candidates',
                'score': best.get('score', 0.0),
                'margin': 0.0,
                'project_code': '',
                'project_name': '',
                'suggested_project_code': best.get(
                    'project_code', ''
                ),
                'suggested_project_name': best.get(
                    'project_name', ''
                ),
                'candidates': [
                    {
                        'project_code': value.get('project_code', ''),
                        'project_name': value.get('project_name', ''),
                        'score': value.get('score', 0.0),
                    }
                    for value in conflicts
                ],
                '_selected_ocr_name': best.get(
                    '_selected_ocr_name', ''
                ),
                '_selected_ocr_code': best.get(
                    '_selected_ocr_code', ''
                ),
            }

        attempts.sort(key=self._match_rank, reverse=True)
        return attempts[0]

    @staticmethod
    def _match_rank(result):
        status_rank = {
            'matched': 3,
            'uncertain': 2,
            'unmatched': 1,
        }.get(result.get('status', ''), 0)
        source_rank = {
            'project_code': 4,
            'project_code_sequence': 3,
            'project_code_ocr_confusable': 3,
            'project_code_ocr_degraded': 3,
            'project_code_fuzzy': 2,
            'project_name': 1,
        }.get(result.get('match_source', ''), 0)

        return (
            status_rank,
            bool(result.get('auto_accepted')),
            source_rank,
            float(result.get('score', 0.0)),
            float(result.get('margin', 0.0)),
        )

    @staticmethod
    def _deduplicate(values):
        result = []
        seen = set()

        for value in values or []:
            text = str(value or '').strip()
            if not text or text in seen:
                continue
            seen.add(text)
            result.append(text)

        return result

    def confirm_review(self, review_result, selected_project_code):
        item = dict(review_result or {})
        status = item.get('status', '')

        if status not in ('review_required', 'unmatched'):
            return self._review_error(item, '当前结果不允许人工确认')

        if item.get('target'):
            return self._review_error(item, '该文件已经生成目标路径')

        source = Path(item.get('source', ''))
        if not source.is_file():
            return self._review_error(item, '原文件不存在或已被移动')

        code = ''.join(str(selected_project_code or '').split()).upper()
        if not code:
            return self._review_error(item, '未选择工程编号')

        project = self.project_service.find_by_code(code)
        if not project:
            return self._review_error(item, '所选工程不在导入项目明细库中')

        return self._rename_with_project(
            image_path=source,
            project_name=project.get('project_name', ''),
            project_code=project.get('project_code', ''),
            report_type=item.get('report_type', ''),
            original=item,
            match={
                'match_source': 'manual_review',
                'score': item.get('match_score', 0.0),
                'margin': item.get('match_margin', 0.0),
                'reason': 'user_confirmed_imported_project',
                'candidates': item.get('candidates', []),
            },
            manual_confirmed=True
        )

    def _rename_with_project(
        self,
        image_path,
        project_name,
        project_code,
        report_type,
        original,
        match,
        manual_confirmed
    ):
        if not project_name:
            return self._review_error(original, '标准工程名称为空')

        if not project_code:
            return self._review_error(original, '标准工程编号为空')

        resolved_type = self._resolve_report_type(
            report_type,
            original
        )

        filename_code = project_code
        filename_tag = ''

        if resolved_type == 'start':
            filename_code = project_code + '_开工'
            filename_tag = '开工'

        if self.output_lock is None:
            target = rename_file(
                image_path,
                self.output_dir,
                project_name,
                filename_code
            )
        else:
            # Keep only the short name-allocation/copy step serialized.
            # OCR and project matching remain parallel, while duplicate
            # targets still receive deterministic _2, _3 suffixes.
            with self.output_lock:
                target = rename_file(
                    image_path,
                    self.output_dir,
                    project_name,
                    filename_code
                )

        return {
            'status': 'success',
            'source': str(image_path),
            'target': str(target),
            'report_type': resolved_type,
            'ocr_project_name': original.get(
                'ocr_project_name',
                original.get('data', {}).get('project_name', '')
                if isinstance(original.get('data'), dict) else ''
            ),
            'ocr_project_code': original.get(
                'ocr_project_code',
                original.get('data', {}).get('project_code', '')
                if isinstance(original.get('data'), dict) else ''
            ),
            'ocr_project_name_candidates': original.get(
                'ocr_project_name_candidates', []
            ),
            'ocr_project_code_candidates': original.get(
                'ocr_project_code_candidates', []
            ),
            'project_name': project_name,
            'project_code': project_code,
            'filename_project_code': project_code,
            'filename_tag': filename_tag,
            'matched': True,
            'manual_confirmed': bool(manual_confirmed),
            'match_source': match.get('match_source', ''),
            'match_score': match.get('score', 0.0),
            'match_margin': match.get('margin', 0.0),
            'match_reason': match.get('reason', ''),
            'candidates': match.get('candidates', []),
        }

    def _resolve_report_type(self, report_type, original):
        if report_type in ('start', 'finish'):
            return report_type

        data = original.get('data', {}) if isinstance(original, dict) else {}
        ocr_code = (
            original.get('ocr_project_code', '')
            if isinstance(original, dict) else ''
        ) or (data.get('project_code', '') if isinstance(data, dict) else '')

        return 'finish' if ocr_code else 'start'

    def _review_error(self, item, message):
        return {
            'status': 'failed',
            'source': item.get('source', ''),
            'target': item.get('target', ''),
            'error': message,
            'report_type': item.get('report_type', ''),
            'ocr_project_name': item.get('ocr_project_name', ''),
            'ocr_project_code': item.get('ocr_project_code', ''),
            'project_name': '',
            'project_code': '',
            'matched': False,
            'manual_confirmed': False,
            'candidates': item.get('candidates', []),
        }
