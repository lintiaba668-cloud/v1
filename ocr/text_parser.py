"""
工程资料OCR文字解析模块
"""

import re


def clean_text(text):
    if not text:
        return ''
    return text.replace(' ', '').replace('\n', '')


def extract_project_name(text):
    """尝试提取工程名称"""
    patterns = [
        r'工程名称[:：]?(.+)',
        r'项目名称[:：]?(.+)'
    ]

    for p in patterns:
        result = re.search(p, text)
        if result:
            return result.group(1).strip()

    return ''


def extract_project_code(text):
    """尝试提取工程编号"""
    patterns = [
        r'工程编号[:：]?([A-Za-z0-9\-_]+)',
        r'编号[:：]?([A-Za-z0-9\-_]+)'
    ]

    for p in patterns:
        result = re.search(p, text)
        if result:
            return result.group(1).strip()

    return ''


def parse_report_text(text):
    text = clean_text(text)

    return {
        'project_name': extract_project_name(text),
        'project_code': extract_project_code(text)
    }
