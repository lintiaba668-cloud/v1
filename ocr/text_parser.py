# -*- coding: utf-8 -*-
"""
工程资料 OCR 文字解析模块。

支持：
- 配网工程开工报告：提取“我方完成”到“项目开工前”之间的工程名称；
- 配网工程竣工验收报告：提取工程名称及工程编号；
- Tesseract PSM 11 稀疏文本输出；
- 标签漏识别时，按电力工程名称特征进行保守兜底。

保持 Python 3.8 / Win7 兼容，不依赖第三方分词组件。
"""

import re
import unicodedata


START_TITLE = '配网工程开工报告'
FINISH_TITLE = '配网工程竣工验收报告'

EXCLUDED_NAME_LINES = (
    START_TITLE,
    FINISH_TITLE,
    '建设单位',
    '设计单位',
    '施工单位',
    '监理单位',
    '主要工程内容',
    '工程造价',
    '开工日期',
    '竣工日期',
    '实际竣工日期',
    '计划竣工日期',
    '请审批',
)

VOLTAGE_PATTERN = re.compile(r'(?:10|35|110|220)\s*[kK][vV]')
MARKED_CODE_PATTERN = re.compile(r'([#A-Z0-9][#A-Z0-9\-]{3,22})')
FALLBACK_CODE_PATTERN = re.compile(
    r'(?<![#A-Z0-9])([A-Z0-9][A-Z0-9\-]{7,22})(?![#A-Z0-9])'
)


def normalize_ocr_text(text):
    if not text:
        return ''

    value = unicodedata.normalize('NFKC', str(text))
    return value.replace('\r\n', '\n').replace('\r', '\n')


def clean_text(text):
    """兼容旧调用：返回去除空白后的连续文本。"""
    value = normalize_ocr_text(text)
    return re.sub(r'\s+', '', value)


def split_ocr_lines(text):
    """保留 OCR 行结构，同时清理无意义边框字符。"""
    lines = []

    for raw_line in normalize_ocr_text(text).split('\n'):
        line = re.sub(r'\s+', '', raw_line)
        line = line.strip('丨|[]【】()（）:：,，。.;；')

        if line:
            lines.append(line)

    return lines


def extract_open_report_name(text):
    """提取开工报告中的工程名称。"""
    compact = clean_text(text)

    patterns = (
        r'我方完成(.{5,120}?)(?:项目开工前|项目开工的|开工前的)',
        r'我方完成(.{5,120}?)(?:准备工作|计划于)',
    )

    for pattern in patterns:
        result = re.search(pattern, compact, flags=re.IGNORECASE)
        if result:
            name = _clean_name(result.group(1))
            if _is_plausible_name(name):
                return name

    return _fallback_project_name(text)


def extract_completion_name(text):
    """提取竣工验收报告中的工程名称。"""
    compact = clean_text(text)

    patterns = (
        r'工程名称(.{5,120}?)(?:工程编号|项目编号|编号|建设单位|施工单位)',
        r'项目名称(.{5,120}?)(?:工程编号|项目编号|编号|建设单位|施工单位)',
    )

    for pattern in patterns:
        result = re.search(pattern, compact, flags=re.IGNORECASE)
        if result:
            name = _clean_name(result.group(1))
            if _is_plausible_name(name):
                return name

    return _fallback_project_name(text)


def _fallback_project_name(text):
    """标签漏识别时，从前部 OCR 行中选择最像工程名称的内容。"""
    lines = split_ocr_lines(text)
    candidates = []

    # 工程名称位于两类报告的顶部，只检查前部内容，避免正文工程量干扰。
    limit = min(len(lines), 24)

    for index in range(limit):
        for span in (1, 2, 3):
            joined = ''.join(lines[index:index + span])
            joined = joined.replace('我方完成', '')

            if '项目开工前' in joined:
                joined = joined.split('项目开工前', 1)[0]

            name = _clean_name(joined)
            score = _name_candidate_score(name, index)

            if score > 0:
                candidates.append((score, name))

    if not candidates:
        return ''

    candidates.sort(key=lambda item: (item[0], len(item[1])), reverse=True)
    best_score, best_name = candidates[0]

    return best_name if best_score >= 45 else ''


def _name_candidate_score(text, line_index):
    if not _is_plausible_name(text):
        return -100

    if any(word in text for word in EXCLUDED_NAME_LINES):
        return -100

    score = 0

    if VOLTAGE_PATTERN.search(text):
        score += 32

    if '工程' in text:
        score += 28

    if any(word in text for word in (
        '台区', '线路', '开闭所', '变电站', '配套',
        '改造', '治理', '新建', '增容', '迁改', '业扩'
    )):
        score += 12

    if any(word in text for word in (
        '福建', '莆田', '荔城', '城厢', '涵江', '秀屿', '仙游'
    )):
        score += 6

    if text.endswith('工程'):
        score += 8

    # 越靠近文档顶部越可信。
    score += max(0, 12 - line_index)

    chinese_count = len(re.findall(r'[\u4e00-\u9fff]', text))
    score += min(chinese_count, 24) / 4.0

    return score


def _is_plausible_name(text):
    if not text:
        return False

    if len(text) < 8 or len(text) > 100:
        return False

    chinese_count = len(re.findall(r'[\u4e00-\u9fff]', text))
    return chinese_count >= 4


def _clean_name(text):
    """清理工程名称 OCR 噪声，但保留 #、数字、电压等级等有效字符。"""
    if not text:
        return ''

    value = normalize_ocr_text(text)
    value = re.sub(r'\s+', '', value)

    remove_words = (
        START_TITLE,
        FINISH_TITLE,
        '工程名称',
        '项目名称',
        '工程编号',
        '项目编号',
        '编号',
        '我方完成',
    )

    for word in remove_words:
        value = value.replace(word, '')

    # 避免把独立工程编号拼到工程名称尾部。
    value = re.sub(r'[#A-Z0-9][#A-Z0-9\-]{3,22}$', '', value)
    value = value.strip('：:，,。.;；|丨[]【】()（）')

    return value


def extract_project_name(text):
    value = normalize_ocr_text(text)
    compact = clean_text(value)

    if '开工报告' in compact or '我方完成' in compact:
        name = extract_open_report_name(value)
        if name:
            return name

    if '竣工验收报告' in compact or '工程编号' in compact:
        name = extract_completion_name(value)
        if name:
            return name

    name = extract_completion_name(value)
    if name:
        return name

    return extract_open_report_name(value)


def _add_code_candidates(candidates, value, marked):
    pattern = MARKED_CODE_PATTERN if marked else FALLBACK_CODE_PATTERN

    for candidate in pattern.findall(value or ''):
        candidates.append((candidate, bool(marked)))


def extract_project_code(text):
    """提取工程编号；无标签时采用严格形态规则，避免正文数字误判。"""
    lines = split_ocr_lines(normalize_ocr_text(text).upper())
    candidates = []

    for index, line in enumerate(lines):
        for marker in ('工程编号', '项目编号', '编号'):
            if marker not in line:
                continue

            tail = line.split(marker, 1)[1]
            _add_code_candidates(candidates, tail, True)

            if index + 1 < len(lines):
                _add_code_candidates(candidates, lines[index + 1], True)

    # 标签漏识别时，只接受较长、数字占比较高的独立编号。
    for line in lines:
        _add_code_candidates(candidates, line, False)

    valid = []

    for candidate, marked in candidates:
        code = re.sub(r'[^#A-Z0-9\-]', '', candidate)
        compact = code.replace('-', '').replace('#', '')
        digit_count = sum(char.isdigit() for char in compact)
        letter_count = sum(char.isalpha() for char in compact)

        if not compact or 'KV' in code or len(code) > 23:
            continue

        if marked:
            if len(compact) < 4 or digit_count < 2:
                continue
        else:
            if digit_count < 6:
                continue
            if digit_count / float(max(1, len(compact))) < 0.45:
                continue

        valid.append((code, marked, digit_count, letter_count))

    if not valid:
        return ''

    valid.sort(
        key=lambda item: (
            item[1],
            10 <= len(item[0]) <= 18,
            item[2],
            1 <= item[3] <= 5,
            '-' in item[0] or '#' in item[0],
            len(item[0]),
        ),
        reverse=True,
    )

    return valid[0][0]


def parse_report_text(text):
    return {
        'project_name': extract_project_name(text),
        'project_code': extract_project_code(text),
    }
