"""
OCR完整处理链。
图片 -> Tesseract/TSV -> 工程信息 -> 文件命名模块。
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

    def _detect_report_type(self, data, text):
        if '开工报告' in text or '我方完成' in text or '项目开工前' in text:
            return 'start'

        if (
            data.get('project_code')
            or '竣工验收报告' in text
            or '实际竣工日期' in text
        ):
            return 'finish'

        return ''

    def _merge_result(self, engine_result, region_result, parsed_result):
        """引擎标准字段优先，文本和坐标结果仅作为降级备用。"""
        engine_name = engine_result.get('project_name', '')
        engine_code = engine_result.get('project_code', '')

        return {
            'project_name': (
                engine_name
                or parsed_result.get('project_name', '')
                or region_result.get('project_name', '')
            ),
            'project_code': (
                engine_code
                or parsed_result.get('project_code', '')
                or region_result.get('project_code', '')
            ),
            'source': (
                'ocr_engine'
                if engine_name or engine_code
                else region_result.get('source', 'text_parser')
            )
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
            data['report_type'] = self._detect_report_type(data, text)

            error = result.get('error_message', '')
            valid = bool(data.get('project_name'))

            if not valid and not error:
                error = 'OCR结果无有效工程名称'

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
