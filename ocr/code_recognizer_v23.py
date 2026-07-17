"""
V2.3 项目编号专用识别模块
针对电力工程编号格式优化
"""

import re


CODE_PATTERNS = [
    r'[A-Z]\d{6,}[A-Z0-9-]*',
    r'\d{8,}[A-Z0-9-]*'
]


def normalize_code(code):
    if not code:
        return ''

    replace_map = {
        'O': '0',
        'I': '1',
        'S': '5'
    }

    for old, new in replace_map.items():
        code = code.replace(old, new)

    return code


def extract_codes(text):
    result = []

    for pattern in CODE_PATTERNS:
        result.extend(re.findall(pattern, text))

    return [normalize_code(x) for x in result]


def best_code(codes):
    if not codes:
        return ''

    return max(codes, key=lambda x: len(x))
