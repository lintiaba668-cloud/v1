"""
V2.1 OCR坐标字段关系解析
利用OCR坐标判断表格左右关系
"""


def find_nearby_value(items, keyword, max_distance=300):
    """
    items:
    [
      {'text':'项目名称','x':100,'y':200},
      {'text':'XXX工程','x':350,'y':200}
    ]
    """
    key_item = None

    for item in items:
        if keyword in item.get('text', ''):
            key_item = item
            break

    if not key_item:
        return ''

    candidates = []

    for item in items:
        if item is key_item:
            continue

        distance = abs(item.get('x', 0) - key_item.get('x', 0))

        if item.get('y', 0) == key_item.get('y', 0) and distance < max_distance:
            candidates.append(item)

    if candidates:
        candidates.sort(key=lambda x: x.get('x', 0))
        return candidates[-1].get('text', '')

    return ''
