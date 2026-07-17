"""
V3.0 Lite 轻量解析流程
优化版：减少复杂评分，提高工程名称和编号稳定性
"""

import re

REMOVE_WORDS = [
    '施工单位',
    '建设单位',
    '监理单位',
    '验收日期'
]

PREFIXES = [
    'B113',
    'C513',
    '181320',
    '5Z'
]


def clean_text(text):
    if not text:
        return ''

    for word in REMOVE_WORDS:
        text = text.split(word)[0]

    return text.replace(':', '').replace('：', '').strip()


def normalize_code(code):
    """
    工程编号标准化。

    支持：
    181320260006-6
    181320260006-11
    181320260006-12
    C5132025Z106

    保留英文、数字、短横线。
    """
    if not code:
        return ''

    code = code.upper()

    # OCR常见误识别修正
    code = code.replace('O', '0')
    code = code.replace('I', '1')
    code = code.replace('S', '5')

    # 去除空格及无关字符
    code = re.sub(r'\s+', '', code)
    code = re.sub(r'[^A-Z0-9-]', '', code)

    return code


def is_power_code(code):
    code = normalize_code(code)
    return any(code.startswith(x) for x in PREFIXES)
