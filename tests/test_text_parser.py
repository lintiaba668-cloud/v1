"""PowerRename OCR parser regression tests."""

from ocr.text_parser import parse_report_text


def test_start_report_name():
    text = '我方完成莆田市110kV线路改造工程项目开工前各项准备工作'
    result = parse_report_text(text)
    assert '莆田市110kV线路改造工程' in result.get('project_name', '')


def test_finish_report_code_keep_symbol():
    text = '''工程名称
莆田10kV吴江线#035B杆工程
工程编号
18132024015D-15'''

    result = parse_report_text(text)

    assert result.get('project_name')
    assert '-' in result.get('project_code', '')


def test_multiline_name_merge():
    text = '''工程名称
莆田荔城井头变10kV吴江线城龙线
#035B分界开关新装业扩配套工程'''

    result = parse_report_text(text)

    assert '城龙线#035B分界开关新装业扩配套工程' in result.get('project_name', '')


def test_finish_sparse_ocr_without_field_labels():
    text = '''
配网工程竣工验收报告
福建莆田萄城区清前村H6变10kV重喜台区治理
1813202400YP04
施工单位
莆田市电力工程有限公司
'''

    result = parse_report_text(text)

    assert '10kV' in result.get('project_name', '')
    assert '台区治理' in result.get('project_name', '')
    assert result.get('project_code') == '1813202400YP04'


def test_finish_name_stops_before_construction_unit_from_real_ocr():
    text = '''
村 载 建 靖 田 萄 城区 清 前 H6 变 10kv 重 台 区 治理
| 单位 “| 施工 莆田 市 电力 工程 有 限 公司
“| 监理 单位 福建 靖 田 疡 源 集 团 有 限 贵 任
和 网 工程 竣工 验收 报告
1813202400YP04
'''

    result = parse_report_text(text)
    name = result.get('project_name', '')

    assert '10kv' in name.lower()
    assert '台区治理' in name
    assert '施工' not in name
    assert '单位' not in name
    assert '莆田市电力工程有限公司' not in name
    assert result.get('project_code') == '1813202400YP04'


def test_start_sparse_ocr_multiline_sentence():
    text = '''
配 网 工程 开工 报告
我 方 完 成 福建靖田荔城区
疯边开闭所公恋10kv重载台区治理工程
项目 开工 前的 各项
准备工作，计划于2025.6.12开工，请审批
'''

    result = parse_report_text(text)

    assert '开闭所' in result.get('project_name', '')
    assert result.get('project_name', '').endswith('治理工程')
    assert result.get('project_code', '') == ''


def test_start_name_discards_text_before_completion_anchor_from_real_ocr():
    text = '''
察 作 : 前 田 荔 源 勘 设计 有 了
方 靖 城 我 完成 福建 田 基 区
边 变 教 俩 开 闭 所 公 10kv 重 台 区 治理 工程
目 项 开工 前 的 各 项
， 准备 工作 计 划 于
号 网 工程 开工 报告
'''

    result = parse_report_text(text)
    name = result.get('project_name', '')

    assert name.startswith('福建')
    assert '开闭所' in name
    assert name.endswith('治理工程')
    assert '荔源勘设计' not in name
    assert '察作' not in name
    assert '我完成' not in name


def test_marked_short_project_code():
    text = '''工程名称
10kV某线路迁改工程
工程编号
#035B'''

    result = parse_report_text(text)
    assert result.get('project_code') == '#035B'


def test_latin_noise_is_not_project_code():
    text = 'Ue Pal Ay SEs BF Wl Ai'
    result = parse_report_text(text)
    assert result.get('project_code', '') == ''
