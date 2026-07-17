"""
V1.7 电力资料模板规则增强
"""

KEYWORDS = {
    'project_code': [
        '项目编号',
        '工程编号',
        '编号'
    ],
    'project_name': [
        '项目名称',
        '工程名称'
    ]
}


def find_field(text, field):
    for key in KEYWORDS[field]:
        if key in text:
            return True
    return False


def is_report_page(text):
    return find_field(text, 'project_name') or find_field(text, 'project_code')
