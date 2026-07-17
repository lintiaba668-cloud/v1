"""
V2.0 电力报告表格字段解析
识别项目名称/项目编号键值关系
"""

PAIR_KEYS = {
    'project_name': ['项目名称', '工程名称'],
    'project_code': ['项目编号', '工程编号']
}


def parse_table_lines(lines):
    result = {
        'project_name': '',
        'project_code': ''
    }

    for line in lines:
        for field, keys in PAIR_KEYS.items():
            for key in keys:
                if key in line:
                    value = line.replace(key, '')
                    value = value.replace(':', '').replace('：', '').strip()
                    if value:
                        result[field] = value

    return result
