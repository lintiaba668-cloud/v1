"""
V2.8 字段区域OCR定位模块
优化版：针对电力工程报告表格字段右侧内容提取
"""

import re

FIELD_MAP = {
    'project_code': ['工程编号', '项目编号', '编号'],
    'project_name': ['工程名称', '项目名称']
}

STOP_WORDS = [
    '建设单位',
    '施工单位',
    '监理单位',
    '验收日期',
    '负责人',
    '开工日期',
    '工程编号',
    '项目编号'
]


def _sort_items(items):
    return sorted(items, key=lambda x: (x.get('y', 0), x.get('x', 0)))


def _same_line(y1, y2, limit=60):
    return abs(y1 - y2) <= limit


def _clean_code(text):
    return re.sub(r'[^A-Za-z0-9\-]', '', text)


def _clean_name(text):
    """工程名称清理，保留编号、井号、括号等有效字符"""
    if not text:
        return ''

    text = text.replace(' ', '')
    text = text.replace('\n', '')
    text = text.replace('工程名称', '')
    text = text.replace('项目名称', '')

    return text.strip('：:，,。')


def locate_field_area(ocr_items, field_type):
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

            if tx > base_x and _same_line(ty, base_y):
                candidates.append(target)
                continue

            if field_type == 'project_name':
                if tx >= base_x - 50 and 0 < ty - base_y < 220:
                    candidates.append(target)
                    continue

            if tx >= base_x - 30 and 0 < ty - base_y < 180:
                candidates.append(target)

        candidates = sorted(candidates, key=lambda x: (x.get('y', 0), x.get('x', 0)))

        for candidate in candidates:
            value = candidate.get('text', '')

            if field_type == 'project_code':
                value = _clean_code(value)
            else:
                value = _clean_name(value)

            if value:
                result.append(value)

    return result


def merge_field_text(items):
    """
    合并多行工程名称。
    根据OCR分块情况添加必要分隔，避免两个字段块粘连。
    """
    result = ''

    for item in items:
        if not item:
            continue

        if not result:
            result = item
            continue

        # 同一工程名称连续块之间增加空格
        # 避免出现：杆035B分界开关
        if result[-1].isdigit() and item[0].isdigit():
            result += ' '
        elif result[-1].isalpha() and item[0].isdigit():
            result += ' '
        elif result[-1] == '杆' and item[0].isdigit():
            result += ' '
        else:
            result += item

    return result
