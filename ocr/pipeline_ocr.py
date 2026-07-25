"""
OCR完整处理链。
图片 -> 模板字段OCR -> 多候选工程信息 -> Excel匹配/文件命名。
"""

import traceback

from .ocr_engine import OCREngine
from .text_parser import parse_report_text
from .field_region_v28 import locate_field_area, merge_field_text


class OCRPipeline(object):
    """OCR业务处理主入口。"""

    def __init__(self):
        self.engine = OCREngine()

    def _extract_region_result(self, items):
        try:
            name_items = locate_field_area(items, 'project_name')
            code_items = locate_field_area(items, 'project_code')

            return {
                'project_name': merge_field_text(name_items),
                'project_code': ''.join(code_items),
                'source': 'field_region'
            }
        except Exception:
            return {
                'project_name': '',
                'project_code': '',
                'source': 'field_region_error'
            }

    def _detect_report_type(self, engine_result, data, text):
        engine_type = engine_result.get('report_type', '')
        if engine_type in ('start', 'finish'):
            return engine_type

        compact = ''.join(str(text or '').split())

        if (
            '开工报告' in compact
            or '我方完成' in compact
            or '我方完' in compact
            or '项目开工前' in compact
        ):
            return 'start'

        if (
            data.get('project_code')
            or '竣工验收报告' in compact
            or '实际竣工日期' in compact
        ):
            return 'finish'

        return ''

    def _merge_result(self, engine_result, region_result, parsed_result):
        engine_name = engine_result.get('project_name', '')
        engine_code = engine_result.get('project_code', '')

        name_candidates = list(
            engine_result.get('project_name_candidates', []) or []
        )
        code_candidates = list(
            engine_result.get('project_code_candidates', []) or []
        )

        project_name = (
            engine_name
            or parsed_result.get('project_name', '')
            or region_result.get('project_name', '')
        )
        project_code = (
            engine_code
            or parsed_result.get('project_code', '')
            or region_result.get('project_code', '')
        )

        if project_name and project_name not in name_candidates:
            name_candidates.insert(0, project_name)
        if project_code and project_code not in code_candidates:
            code_candidates.insert(0, project_code)

        return {
            'project_name': project_name,
            'project_code': project_code,
            'project_name_candidates': name_candidates,
            'project_code_candidates': code_candidates,
            'source': engine_result.get(
                'recognition_source',
                'ocr_engine' if project_name or project_code else region_result.get(
                    'source', 'text_parser'
                )
            ),
            'rotation_angle': engine_result.get('rotation_angle', 0),
        }

    def process(self, image):
        try:
            result = self.engine.recognize(image)

            if not result:
                return {
                    'text': '',
                    'data': {},
                    'valid': False,
                    'items': [],
                    'error': 'OCR返回为空'
                }

            items = result.get('items', [])
            text = result.get('raw_text', '')
            region_result = self._extract_region_result(items)
            parsed_result = parse_report_text(text)
            data = self._merge_result(result, region_result, parsed_result)
            data['report_type'] = self._detect_report_type(result, data, text)

            error = result.get('error_message', '')
            report_type = data.get('report_type', '')
            names = data.get('project_name_candidates', [])
            codes = data.get('project_code_candidates', [])

            # A non-empty OCR string is no longer sufficient. It must come
            # from a recognized report template and from the target field.
            valid = (
                report_type == 'start' and bool(names)
            ) or (
                report_type == 'finish' and bool(names or codes)
            )

            if not valid and not error:
                error = '未从开工/竣工报告目标字段取得有效候选'

            return {
                'text': text,
                'data': data,
                'valid': valid,
                'items': items,
                'error': error
            }

        except Exception as exc:
            return {
                'text': '',
                'data': {},
                'valid': False,
                'items': [],
                'error': str(exc),
                'trace': traceback.format_exc()
            }
