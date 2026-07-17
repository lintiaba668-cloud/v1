"""
OCR识别置信度基础模块
"""


def check_result(result):
    if not result:
        return False

    return bool(result.get('project_name'))
