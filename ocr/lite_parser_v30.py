"""
V3.0 Lite 轻量解析流程
减少复杂评分，提高稳定性
"""

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
    if not code:
        return ''

    code = code.upper()
    code = code.replace('O', '0').replace('I', '1').replace('S', '5')

    return code


def is_power_code(code):
    return any(code.startswith(x) for x in PREFIXES)
