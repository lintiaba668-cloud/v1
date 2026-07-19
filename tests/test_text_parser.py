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
