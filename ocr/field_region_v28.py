"""
V2.8 字段区域OCR定位模块
针对电力工程报告表格字段右侧内容提取
"""

FIELD_MAP = {
    'project_code': ['工程编号', '项目编号', '编号'],
    'project_name': ['工程名称', '项目名称']
}


def locate_field_area(ocr_items, field_type):
    """
    ocr_items:
    [{'text':'工程编号','x':100,'y':200}]
    返回字段右侧候选区域
    """
    result = []

    keys = FIELD_MAP.get(field_type, [])

    for item in ocr_items:
        text = item.get('text', '')
        if any(k in text for k in keys):
            base_x = item.get('x', 0)
            base_y = item.get('y', 0)

            for target in ocr_items:
                if target is item:
                    continue

                if (target.get('x', 0) > base_x and
                    abs(target.get('y', 0)-base_y) < 50):
                    result.append(target.get('text', ''))

    return result
