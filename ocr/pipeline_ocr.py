"""
OCR完整处理链
图片 -> OCR文字+坐标 -> 工程信息

PowerRename V1
生产级处理逻辑：
1. 优先使用字段区域定位识别竣工验收报告
2. 开工报告使用全文模板解析
3. 任一识别链失败自动降级
"""

import traceback

from .ocr_engine import OCREngine
from .text_parser import parse_report_text
from .field_region_v28 import locate_field_area, merge_field_text


class OCRPipeline:
    """OCR业务处理主入口"""

    def __init__(self):
        self.engine = OCREngine()

    def _extract_region_result(self, items):
        """
        基于OCR坐标结果提取表格字段。

        主要用于竣工验收报告：
        工程名称 + 工程编号。
        """
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

    def _merge_result(self, region, parsed):
        """
        合并字段定位结果和全文解析结果。

        原则：
        坐标结果优先；文本解析作为备用。
        """
        return {
            'project_name': region.get('project_name') or parsed.get('project_name', ''),
            'project_code': region.get('project_code') or parsed.get('project_code', ''),
            'source': region.get('source', 'text_parser')
        }

    def process(self, image):
        """
        OCR主流程。

        参数：
            image: 图片路径

        返回：
            text: OCR全文
            data: 工程字段
            valid: 是否成功识别
            items: OCR坐标信息
        """
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

            valid = bool(data.get('project_name'))

            return {
                'text': text,
                'data': data,
                'valid': valid,
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
