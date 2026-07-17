"""
V2.6 电力工程编号纠错增强
"""

import re

POWER_PREFIX = [
    'B113',
    'C513',
    '181320',
    '5Z'
]


def fix_power_code(code):
    if not code:
        return ''

    code = code.upper()

    replace = {
        'O': '0',
        'I': '1',
        'S': '5'
    }

    for a, b in replace.items():
        code = code.replace(a, b)

    # 常见OCR将C识别成5，B识别异常
    if code.startswith('5513'):
        code = 'C' + code[2:]

    return code


def code_confidence(code):
    score = 0

    if any(code.startswith(x) for x in POWER_PREFIX):
        score += 50

    if re.search(r'\d{4}', code):
        score += 20

    if 5 <= len(code) <= 20:
        score += 20

    return score
