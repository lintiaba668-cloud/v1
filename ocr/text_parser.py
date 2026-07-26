# -*- coding: utf-8 -*-
"""
工程资料 OCR 文字解析模块。

支持：
- 配网工程开工报告：严格提取“我方完成”到“项目开工前”之间内容；
- 配网工程竣工验收报告：提取工程名称及工程编号；
- Tesseract PSM 11 稀疏文本输出；
- 标签漏识别时，按电力工程名称特征进行保守兜底；
- 遇建设/设计/施工/监理单位等字段时停止工程名称拼接。

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

NAME_BOUNDARIES = (
    '工程编号',
    '项目编号',
    '建设单位',
    '设计单位',
    '施工单位',
    '监理单位',
    '主要工程内容',
    '主要工程',
    '工程造价',
    '开工日期',
    '竣工日期',
    '实际竣工日期',
    '计划竣工日期',
    '施工',
    '监理',
    '单位',
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
        line = line.strip('丨|[]【】()（）:：,，。.;；“”\'')

        if line:
            lines.append(line)

    return lines


def extract_open_report_name(text):
    """提取开工报告中的工程名称，不允许包含“完成”之前内容。"""
    compact = clean_text(text)

    # 手机照片中“我方完成”可能丢字，或把“完”识别成形近的“究”。
    anchor = r'(?:我方完成|我方究成|我方完|我完成|方完成|方完)'

    # Preserve line geometry before flattening the OCR text. Sparse-text OCR
    # often emits the name fragment to the right of "我方完成" either before
    # or after the anchor line. The compact regex below cannot recover that
    # reading-order inversion once all newlines have been removed.
    wrapped = _extract_wrapped_start_name(text, anchor)
    if wrapped:
        return wrapped

    patterns = (
        anchor + r'(.{5,120}?)(?:项目开工前|目项开工前|项目开工|目项开工|开工前)',
        anchor + r'(.{5,120}?)(?:准备工作|计划于)',
    )

    for pattern in patterns:
        result = re.search(pattern, compact, flags=re.IGNORECASE)
        if result:
            name = _clean_name(result.group(1))
            if (
                '项目开工前' not in name
                and '开工前的各项' not in name
                and _is_plausible_name(name)
            ):
                return name

    return _fallback_project_name(text, report_type='start')


def _extract_wrapped_start_name(text, anchor):
    """Recover a start-report name whose visual lines precede the anchor.

    Sparse-text OCR sometimes emits the two long project-name lines before
    ``我方完成`` even though they are visually to its right. A short
    ``套工程`` suffix may then appear immediately after the anchor.
    """
    lines = split_ocr_lines(text)

    for index, line in enumerate(lines):
        anchor_match = re.search(anchor, line)
        if not anchor_match:
            continue

        fragments = []
        for offset in (1, 2):
            position = index - offset
            if position < 0:
                break
            value = lines[position]
            if value.startswith('致') or value.endswith('有限公司'):
                break
            if (
                not _contains_name_boundary(value)
                and (
                    VOLTAGE_PATTERN.search(value)
                    or any(word in value for word in (
                        '工程', '线路', '台区', '开闭所', '环网柜',
                        '分界开关', '配套', '业扩', '改造', '新建',
                    ))
                )
            ):
                fragments.append(value)

        inline = line[anchor_match.end():]
        if inline:
            fragments.append(inline)

        if index + 1 < len(lines):
            possible_suffix = lines[index + 1]
            if (
                len(possible_suffix) <= 30
                and '工程' in possible_suffix
                and not possible_suffix.startswith(('项目开工', '目项开工'))
            ):
                fragments.append(possible_suffix)

        if not fragments:
            continue

        # A geographic prefix is stronger than voltage: an inline prefix such
        # as "福建莆田..." can be followed by the voltage-bearing continuation.
        # Stable sorting keeps OCR order for the remaining suffix fragments.
        fragments.sort(
            key=lambda value: (
                bool(re.match(
                    r'^(?:福建|莆田|城厢|荔城|涵江|秀屿|仙游)',
                    value,
                )),
                bool(VOLTAGE_PATTERN.search(value)),
            ),
            reverse=True,
        )
        name = _clean_name(''.join(fragments))
        if _is_plausible_name(name):
            return name

    return ''


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

    return _fallback_project_name(text, report_type='finish')


def _fallback_project_name(text, report_type=''):
    """标签漏识别时，从文档前部选择工程名称候选。"""
    lines = split_ocr_lines(text)
    candidates = []
    limit = min(len(lines), 24)

    for index in range(limit):
        joined = ''

        for span in (1, 2, 3):
            next_index = index + span - 1
            if next_index >= limit:
                break

            next_line = lines[next_index]

            if span > 1 and _contains_name_boundary(next_line):
                break

            joined += next_line
            candidate = joined

            if report_type == 'start':
                candidate = _extract_after_completion_anchor(candidate)
                if not candidate:
                    continue

            name = _clean_name(candidate)
            score = _name_candidate_score(name, index)

            if score > 0:
                candidates.append((score, name))

    if not candidates:
        return ''

    candidates.sort(key=lambda item: (item[0], len(item[1])), reverse=True)
    best_score, best_name = candidates[0]

    return best_name if best_score >= 45 else ''


def _extract_after_completion_anchor(text):
    """开工报告兜底时也必须丢弃“完成”之前的文字。"""
    compact = clean_text(text)
    match = re.search(
        r'(?:我方完成|我方究成|我方完|我完成|方完成|方完)(.+)$',
        compact,
    )

    if not match:
        return ''

    value = match.group(1)

    for marker in ('项目开工前', '目项开工前', '项目开工', '目项开工', '开工前'):
        if marker in value:
            value = value.split(marker, 1)[0]
            break

    return value


def _contains_name_boundary(text):
    compact = clean_text(text)
    return any(word in compact for word in NAME_BOUNDARIES)


def _truncate_at_boundary(text):
    value = text
    positions = [
        value.find(word)
        for word in NAME_BOUNDARIES
        if value.find(word) >= 0
    ]

    if positions:
        value = value[:min(positions)]

    return value


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
        '我方究成',
        '我方完',
        '我完成',
        '方完成',
        '方完',
    )

    for word in remove_words:
        value = value.replace(word, '')

    value = _truncate_at_boundary(value)
    value = re.sub(r'[#A-Z0-9][#A-Z0-9\-]{3,22}$', '', value)
    value = value.strip('：:，,。.;；|丨[]【】()（）“”\'')

    return value


def clean_project_name_candidate(text):
    """Public field-cleaning API used by template OCR and legacy callers."""
    return _clean_name(text)


def extract_project_name(text):
    value = normalize_ocr_text(text)
    compact = clean_text(value)

    if '开工报告' in compact or any(
        marker in compact
        for marker in (
            '我方完成', '我方究成', '我方完',
            '我完成', '方完成', '方完',
        )
    ):
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
