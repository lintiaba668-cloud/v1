"""
V1.6 OCR多结果融合
用于提升竣工验收报告识别稳定性
"""


def normalize_text(text):
    if not text:
        return ''

    replacements = {
        'Ｏ': '0',
        'I': '1'
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text.strip()


def merge_results(results):
    """
    results:
    [
      {'project_name':'','project_code':''},
      ...
    ]
    """
    name = ''
    code = ''

    for item in results:
        if len(item.get('project_name','')) > len(name):
            name = item.get('project_name','')
        if len(item.get('project_code','')) > len(code):
            code = item.get('project_code','')

    return {
        'project_name': normalize_text(name),
        'project_code': normalize_text(code)
    }
