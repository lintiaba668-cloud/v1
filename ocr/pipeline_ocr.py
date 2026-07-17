"""
OCR完整处理链
图片 -> OCR文字+坐标 -> 工程信息
Win7兼容版
"""

from .ocr_engine import OCREngine
from .text_parser import parse_report_text
from .field_region_v28 import locate_field_area, merge_field_text


class OCRPipeline:
    def __init__(self):
        self.engine = OCREngine()

    def process(self, image):
        result = self.engine.recognize(image)

        items = result.get('items', [])
        text = result.get('raw_text', '')

        # 优先使用坐标区域提取
        project_name_items = locate_field_area(items, 'project_name')
        project_code_items = locate_field_area(items, 'project_code')

        project_name = merge_field_text(project_name_items)
        project_code = ''.join(project_code_items)

        # 坐标提取失败时使用文本模板解析
        if not project_name or not project_code:
            parsed = parse_report_text(text)
            project_name = project_name or parsed.get('project_name', '')
            project_code = project_code or parsed.get('project_code', '')

        data = {
            'project_name': project_name,
            'project_code': project_code
        }

        valid = bool(project_name)

        return {
            'text': text,
            'data': data,
            'valid': valid,
            'items': items
        }
