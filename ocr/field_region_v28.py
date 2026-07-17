"""
V2.8 字段区域OCR定位模块
优化版：针对电力工程报告表格字段右侧内容提取
"""

FIELD_MAP = {
    'project_code': ['工程编号', '项目编号', '编号'],
    'project_name': ['工程名称', '项目名称']
}

STOP_WORDS = [
    '建设单位',
    '施工单位',
    '监理单位',
    '验收日期',
    '负责人'
]


def _sort_items(items):
    """OCR结果按页面阅读顺序排序"""
    return sorted(items, key=lambda x: (x.get('y', 0), x.get('x', 0)))


def locate_field_area(ocr_items, field_type):
    """
    提取字段右侧完整区域。

    支持：
    - 多行工程名称
    - 工程编号后带 -6/-11/-12 等格式
    - OCR坐标轻微偏移
    """
    result = []
    items = _sort_items(ocr_items)

    keys = FIELD_MAP.get(field_type, [])

    for index, item in enumerate(items):
        text = item.get('text', '')

        if not any(k in text for k in keys):
            continue

        base_x = item.get('x', 0)
        base_y = item.get('y', 0)

        candidates = []

        for target in items[index + 1:]:
            target_text = target.get('text', '')
            tx = target.get('x', 0)
            ty = target.get('y', 0)

            if any(stop in target_text for stop in STOP_WORDS):
                break

            # 同行右侧或下一行同区域
            if tx > base_x and abs(ty - base_y) < 120:
                candidates.append(target_text)

        result.extend(candidates)

    return result
