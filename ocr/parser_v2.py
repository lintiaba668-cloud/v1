"""
OCR解析器 V1.8
电力工程开竣工报告智能解析
"""

import re

from .patterns import PROJECT_NAME_KEYS, PROJECT_CODE_KEYS


STOP_WORDS = [
    '施工单位',
    '建设单位',
    '监理单位',
    '验收日期',
    '开工日期',
    '竣工日期',
    '项目编号',
    '工程编号'
]

INVALID_WORDS = [
    '我方完成',
    '项目开工前的各项准备工作',
    '项目开工前',
    '各项准备工作',
    '申请批准',
    '计划于',
    '工程名称',
    '项目名称',
    '工程编号',
    '项目编号'
]


def clean_project_name(value):
    for word in INVALID_WORDS:
        value = value.replace(word, '')

    for word in STOP_WORDS:
        if word in value:
            value = value.split(word)[0]

    value = value.replace('：', ':')
    return value.strip(' ：:，。,. ')


def extract_after_key(text, keys):
    for key in keys:
        pattern = rf'{key}[：:]?\s*([^\n]+)'
        match = re.search(pattern, text)
        if match:
            value = clean_project_name(match.group(1))
            if value:
                return value
    return ''


def extract_code(text):
    value = extract_after_key(text, PROJECT_CODE_KEYS)

    candidates = []
    if value:
        candidates.append(value)

    candidates.extend(re.findall(r'[A-Za-z0-9]{6,}', text))

    best = ''
    for item in candidates:
        item = item.replace('O', '0').replace('I', '1')
        if len(item) >= 6 and len(item) > len(best):
            best = item

    return best


def extract_from_report_sentence(text):
    pattern = r'(?:我方完成|完成)\s*([^，。\n]+?(?:工程|线路|改造|大修|优化))'
    match = re.search(pattern, text)

    if match:
        return clean_project_name(match.group(1))

    return ''


def parse_engineering_text(text):
    project_name = extract_after_key(text, PROJECT_NAME_KEYS)

    if not project_name:
        project_name = extract_from_report_sentence(text)

    return {
        'project_name': project_name,
        'project_code': extract_code(text)
    }
