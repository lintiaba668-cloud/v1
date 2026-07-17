"""
OCR解析器 V1.3
电力工程开竣工报告增强解析
"""

import re

from .patterns import PROJECT_NAME_KEYS, PROJECT_CODE_KEYS


INVALID_WORDS = [
    '我方完成',
    '项目开工前的各项准备工作',
    '项目开工前',
    '各项准备工作',
    '申请批准',
    '计划于',
    '工程名称',
    '工程编号'
]


def clean_project_name(value):
    for word in INVALID_WORDS:
        value = value.replace(word, '')

    value = value.replace('：', ':')
    value = value.strip(' ：:，。,.')
    return value.strip()


def extract_after_key(text, keys):
    for key in keys:
        pattern = rf'{key}[：:]?\s*([^\n]+)'
        match = re.search(pattern, text)
        if match:
            return clean_project_name(match.group(1))
    return ''


def extract_code(text):
    value = extract_after_key(text, PROJECT_CODE_KEYS)
    if value:
        match = re.search(r'[A-Za-z0-9]{6,}', value)
        if match:
            return match.group(0)

    match = re.search(r'\b[A-Z]\d{6,}[A-Z0-9]*\b', text)
    return match.group(0) if match else ''


def extract_from_report_sentence(text):
    """
    开工报告语义：
    我方完成 XXX工程
    """
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
