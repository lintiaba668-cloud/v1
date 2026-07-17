"""
V2.5 竣工报告字段增强解析
"""

import re


CODE_HINTS = [
    '工程编号',
    '项目编号',
    '编号'
]

NAME_HINTS = [
    '工程名称',
    '项目名称'
]


def clean_code(code):
    if not code:
        return ''

    table = str.maketrans({
        'O': '0',
        'I': '1',
        'S': '5'
    })

    return code.translate(table).strip()


def find_field_value(lines, keywords):
    for i, line in enumerate(lines):
        for key in keywords:
            if key in line:
                value = line.replace(key, '')
                value = value.replace(':', '').replace('：', '').strip()
                if value:
                    return value
                if i + 1 < len(lines):
                    return lines[i + 1].strip()
    return ''


def extract_code(lines):
    value = find_field_value(lines, CODE_HINTS)
    candidates = re.findall(r'[A-Za-z0-9-]{5,}', value)

    if candidates:
        return clean_code(max(candidates, key=len))

    return ''


def extract_name(lines):
    value = find_field_value(lines, NAME_HINTS)

    stops = ['施工单位', '建设单位', '监理单位', '验收日期']

    for stop in stops:
        value = value.split(stop)[0]

    return value.strip()
