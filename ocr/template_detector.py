"""
V1.4 电力报告模板检测
自动判断开工报告/竣工验收报告
"""


def detect_template(text):
    score = {
        'startup': 0,
        'completion': 0
    }

    keywords = {
        'startup': ['开工报告', '我方完成', '开工前'],
        'completion': ['竣工验收报告', '工程编号', '工程名称', '验收日期']
    }

    for key, words in keywords.items():
        for word in words:
            if word in text:
                score[key] += 1

    return max(score, key=score.get)
