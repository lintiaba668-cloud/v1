"""
工程资料OCR文字解析模块
支持开工报告、竣工验收报告模板
优化版
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
        r'我方完成(.+?)开工前的',
        r'我方完成(.+?)，?项目开工'
    ]

    for pattern in patterns:
        result = re.search(pattern, text)
        if result:
            return _clean_name(result.group(1))

    return ''


def extract_completion_name(text):
    """
    竣工验收报告：
    提取工程名称栏右侧内容。
    """
    patterns = [
        r'工程名称(.+?)(?:工程编号|编号|建设单位|施工单位)',
        r'项目名称(.+?)(?:工程编号|编号|建设单位|施工单位)'
    ]

    for pattern in patterns:
        result = re.search(pattern, text)
        if result:
            return _clean_name(result.group(1))

    return ''


def _clean_name(text):
    """清理工程名称OCR噪声"""
    if not text:
        return ''

    remove_words = [
        '工程名称',
        '项目名称',
        '工程编号',
        '编号'
    ]

    for word in remove_words:
        text = text.replace(word, '')

    return text.strip('：:，,。 ')


def extract_project_name(text):
    name = extract_completion_name(text)
    if name:
        return name

    return extract_open_report_name(text)


def extract_project_code(text):
    """
    工程编号提取。
    支持：
    ABC123
    ABC123-6
    ABC123-11
    ABC123-12
    """
    patterns = [
        r'工程编号([A-Za-z0-9\-_]+)',
        r'项目编号([A-Za-z0-9\-_]+)',
        r'编号([A-Za-z0-9\-_]+)'
    ]

    for pattern in patterns:
        result = re.search(pattern, text)
        if result:
            return re.sub(r'[^A-Za-z0-9\-]', '', result.group(1))

    return ''


def parse_report_text(text):
    text = clean_text(text)

    return {
        'project_name': extract_project_name(text),
        'project_code': extract_project_code(text)
    }
