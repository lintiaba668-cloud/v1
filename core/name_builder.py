"""
V1.5 文件命名规则
规则：
有项目编号 -> 项目编号+项目名称
无项目编号 -> 项目名称
"""

import re

INVALID_CHARS = r'\\/:*?"<>|'


def clean_filename(value):
    for char in INVALID_CHARS:
        value = value.replace(char, '')
    return value.strip()


def build_filename(project_name, project_code=''):
    project_name = clean_filename(project_name)
    project_code = clean_filename(project_code)

    if project_code:
        return f'{project_code}{project_name}'

    return project_name


def add_duplicate_suffix(filename, exists):
    if filename not in exists:
        return filename

    index = 2
    while f'{filename}_{index}' in exists:
        index += 1

    return f'{filename}_{index}'
