"""
OCR完整处理链
图片 -> OCR -> 工程信息 -> 文件命名模块

保持原OCR识别逻辑不变，仅增加统一业务输出字段。
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
        """判断报告类型。

        当前软件只支持两类：
        start  开工报告
        finish 竣工验收报告
        """
        if data.get('project_code'):
            return 'finish'

        if '我方完成' in text or '项目开工前' in text:
            return 'start'

        return ''

    def _merge_result(self, region, parsed):
        return {
            'project_name': region.get('project_name') or parsed.get('project_name', ''),
            'project_code': region.get('project_code') or parsed.get('project_code', ''),
            'source': region.get('source', 'text_parser')
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
            data = self._merge_result(region_result, parsed_result)

            data['report_type'] = self._detect_report_type(data, text)

            return {
                'text': text,
                'data': data,
                'valid': bool(data.get('project_name')),
                'items': items,
                'error': ''
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
