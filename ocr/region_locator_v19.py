"""
V1.9 OCR关键区域定位
自动寻找项目名称/项目编号附近区域
"""

import re

FIELD_WORDS = [
    '项目名称',
    '工程名称',
    '项目编号',
    '工程编号'
]


def locate_regions(text_lines):
    """
    根据OCR行结果定位关键字段附近文本
    text_lines: OCR分行列表
    """
    regions = []

    for index, line in enumerate(text_lines):
        for word in FIELD_WORDS:
            if word in line:
                start = max(0, index - 1)
                end = min(len(text_lines), index + 3)
                regions.append(text_lines[start:end])

    return regions


def merge_region_text(regions):
    result = []

    for region in regions:
        result.extend(region)

    return '\n'.join(result)
