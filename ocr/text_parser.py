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
    pattern = r'我方完成(.+?)项目开工前'
    result = re.search(pattern, text)
    if result:
        return result.group(1).strip('：:，,')
    return ''


def extract_project_name(text):
    """工程名称提取"""
    patterns = [
        r'工程名称[:：]?(.+)',
        r'项目名称[:：]?(.+)'
    ]

    for p in patterns:
        result = re.search(p, text)
        if result:
            return result.group(1).strip()

    # 开工报告模板备用
    return extract_open_report_name(text)


def extract_project_code(text):
    """工程编号提取，支持-11/-12格式"""
    patterns = [
        r'工程编号[:：]?([A-Za-z0-9\-_]+)',
        r'项目编号[:：]?([A-Za-z0-9\-_]+)',
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
