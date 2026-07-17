"""
V1.8 OCR结果评分引擎
用于选择最佳项目编号和项目名称
"""

import re


def code_score(code, text=''):
    score = 0

    if not code:
        return score

    if len(code) >= 6:
        score += 20

    if re.search(r'\d{4}', code):
        score += 20

    if re.search(r'[A-Za-z]', code):
        score += 20

    if code in text:
        score += 40

    return score


def name_score(name):
    score = 0

    if not name:
        return 0

    if len(name) > 8:
        score += 30

    keywords = ['工程', '线路', '改造', '大修', '优化', '迁改']

    for word in keywords:
        if word in name:
            score += 10

    return min(score, 100)
