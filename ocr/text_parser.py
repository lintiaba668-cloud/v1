"""
工程资料OCR文字解析模块
支持开工报告、竣工验收报告模板
"""

import re


def clean_text(text):
    if not text:
        return ''
    return text.replace(' ', '').replace('\n', '')


def extract_open_report_name(text):
    """
    开工报告：
    提取“我方完成”到“项目开工前”之间内容。
    """
    patterns = [
        r'我方完成(.+?)项目开工前',
        r'我方完成(.+?)开工前'
    ]

    for pattern in patterns:
        result = re.search(pattern, text)
        if result:
            return result.group(1).strip('：:，,')

    return ''


def extract_completion_name(text):
    """竣工验收报告工程名称提取"""
    patterns = [
        r'工程名称[:：]?(.+?)(?:工程编号|编号|建设单位|施工单位|$)',
        r'项目名称[:：]?(.+?)(?:工程编号|编号|建设单位|施工单位|$)'
    ]

    for pattern in patterns:
        result = re.search(pattern, text)
        if result:
            return result.group(1).strip()

    return ''


def extract_project_name(text):
    """工程名称提取"""
    name = extract_completion_name(text)
    if name:
        return name

    return extract_open_report_name(text)


def extract_project_code(text):
    """工程编号提取，支持-6/-11/-12格式"""
    patterns = [
        r'工程编号[:：]?([A-Za-z0-9\-_]+)',
        r'项目编号[:：]?([A-Za-z0-9\-_]+)',
        r'编号[:：]?([A-Za-z0-9\-_]+)'
    ]

    for pattern in patterns:
        result = re.search(pattern, text)
        if result:
            return result.group(1).strip()

    return ''


def parse_report_text(text):
    text = clean_text(text)

    return {
        'project_name': extract_project_name(text),
        'project_code': extract_project_code(text)
    }
