"""
OCR解析器 V2
增强工程名称、工程编号提取
"""

import re

from .patterns import PROJECT_NAME_KEYS, PROJECT_CODE_KEYS


def extract_after_key(text, keys):
    for key in keys:
        pattern = rf'{key}[：:]?\s*(.+)'
        match = re.search(pattern, text)
        if match:
            value = match.group(1).strip()
            if value:
                return value.split('\n')[0].strip()
    return ''


def parse_engineering_text(text):
    return {
        'project_name': extract_after_key(text, PROJECT_NAME_KEYS),
        'project_code': extract_after_key(text, PROJECT_CODE_KEYS)
    }
