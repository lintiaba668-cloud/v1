"""
V1.4 OCR结果置信度评分
"""


def score_result(project_name, project_code):
    score = 0

    if project_name:
        score += 50
    if project_code:
        score += 40
    if len(project_name) > 8:
        score += 10

    return min(score, 100)


def check_result(result):
    if not result:
        return False

    return bool(result.get('project_name'))
