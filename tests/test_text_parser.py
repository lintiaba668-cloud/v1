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
