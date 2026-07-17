"""
电力工程资料OCR关键词规则
"""

PROJECT_NAME_KEYS = [
    '工程名称',
    '项目名称',
    '工程项目名称'
]

PROJECT_CODE_KEYS = [
    '工程编号',
    '项目编号',
    '编号'
]


def find_key(text, keys):
    for key in keys:
        if key in text:
            return key
    return ''
