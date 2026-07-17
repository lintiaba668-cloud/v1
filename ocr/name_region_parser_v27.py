"""
V2.7 工程名称区域增强解析
"""

STOP_WORDS = [
    '施工单位',
    '建设单位',
    '监理单位',
    '验收日期',
    '开工日期',
    '竣工日期'
]

NAME_KEYS = [
    '工程名称',
    '项目名称'
]


def clean_name(text):
    if not text:
        return ''

    for key in NAME_KEYS:
        text = text.replace(key, '')

    for stop in STOP_WORDS:
        if stop in text:
            text = text.split(stop)[0]

    return text.replace(':', '').replace('：', '').strip()


def choose_name(candidates):
    if not candidates:
        return ''

    score = []

    keywords = ['工程', '线路', '改造', '大修', '优化', '迁改']

    for item in candidates:
        value = clean_name(item)
        s = len(value)
        for k in keywords:
            if k in value:
                s += 20
        score.append((s, value))

    return max(score, key=lambda x: x[0])[1]
