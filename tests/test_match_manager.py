# -*- coding: utf-8 -*-

"""Tests for imported project-detail matching decisions."""

from project.match_manager import MatchManager
from project.match_strategy import PowerProjectMatchStrategy


class FakeProjectService:

    def __init__(self, projects):
        self.projects = list(projects)

    def list_projects(self):
        return list(self.projects)

    def find_by_code(self, code):
        for project in self.projects:
            if project.get('project_code') == code:
                return project
        return None


def test_exact_project_code_has_highest_priority():
    service = FakeProjectService([
        {
            'project_code': '1813202400YP04',
            'project_name': '莆田荔城220kV上庄变10kV福岭线#01杆迁改工程'
        }
    ])
    manager = MatchManager(project_service=service)

    result = manager.match_project(
        ocr_text='完全错误的名称',
        project_code=' 1813202400YP04 '
    )

    assert result['status'] == 'matched'
    assert result['match_source'] == 'project_code'
    assert result['project_code'] == '1813202400YP04'
    assert result['score'] == 100.0


def test_unique_one_edit_project_code_is_corrected():
    service = FakeProjectService([
        {
            'project_code': 'B1132025Z497',
            'project_name': '莆田荔城110kV城厢变10kV东江线七步#27箱式变低压线路大修'
        },
        {
            'project_code': '181320260001-1',
            'project_name': '其他工程'
        },
    ])
    manager = MatchManager(project_service=service)

    result = manager.match_project(
        ocr_text='',
        project_code='B1132025Z4A7'
    )

    assert result['status'] == 'matched'
    assert result['match_source'] == 'project_code_fuzzy'
    assert result['project_code'] == 'B1132025Z497'
    assert result['score'] == 98.0


def test_unique_truncated_project_code_prefix_is_corrected():
    service = FakeProjectService([
        {
            'project_code': '181320260001-7',
            'project_name': (
                '莆田荔城城东变10kV岳公线#1环网柜、'
                '白埕线#1环网柜新建业扩配套工程'
            ),
        },
        {
            'project_code': '181320260006-7',
            'project_name': '其他工程',
        },
    ])
    manager = MatchManager(project_service=service)

    result = manager.match_project(
        ocr_text='',
        project_code='1320260001-7',
    )

    assert result['status'] == 'matched'
    assert result['match_source'] == 'project_code_fuzzy'
    assert result['project_code'] == '181320260001-7'


def test_ambiguous_truncated_project_code_is_not_auto_accepted():
    service = FakeProjectService([
        {'project_code': '181320260001-7', 'project_name': '工程一'},
        {'project_code': '191320260001-7', 'project_name': '工程二'},
    ])
    manager = MatchManager(project_service=service)

    result = manager.match_project(
        ocr_text='',
        project_code='1320260001-7',
    )

    assert result['status'] == 'unmatched'
    assert result['auto_accepted'] is False


def test_ambiguous_fuzzy_code_is_not_auto_accepted():
    service = FakeProjectService([
        {'project_code': 'ABC1234567', 'project_name': '工程一'},
        {'project_code': 'ABC1234568', 'project_name': '工程二'},
    ])
    manager = MatchManager(project_service=service)

    result = manager.match_project(
        ocr_text='',
        project_code='ABC1234569'
    )

    assert result['status'] == 'unmatched'
    assert result['auto_accepted'] is False


def test_ocr_confusable_code_outweighs_generic_one_edit_candidates():
    service = FakeProjectService([
        {
            'project_code': '1813202300LN',
            'project_name': 'expected project',
        },
        {
            'project_code': '18132023001K',
            'project_name': 'generic one-edit neighbor',
        },
        {
            'project_code': '18132023006N',
            'project_name': 'another generic one-edit neighbor',
        },
    ])
    manager = MatchManager(project_service=service)

    result = manager.match_project(
        ocr_text='',
        project_code='18132023001N',
    )

    assert result['status'] == 'matched'
    assert result['match_source'] == 'project_code_ocr_confusable'
    assert result['project_code'] == '1813202300LN'
    assert result['score'] == 99.0


def test_unique_code_allows_leading_loss_plus_ocr_glyph_errors():
    service = FakeProjectService([
        {
            'project_code': 'C5132026Z00Z',
            'project_name': (
                '莆田荔城区110kV黄石变10kV惠洋线'
                '沙堤村#8变A03至A07杆迁改工程'
            ),
        },
        {
            'project_code': 'C5132026Z015',
            'project_name': '其他迁改工程',
        },
    ])
    manager = MatchManager(project_service=service)

    result = manager.match_project(project_code='51320262007')

    assert result['status'] == 'matched'
    assert result['project_code'] == 'C5132026Z00Z'
    assert result['match_source'] == 'project_code_ocr_degraded'


def test_degraded_code_is_not_accepted_when_multiple_projects_fit():
    service = FakeProjectService([
        {
            'project_code': 'C5132026Z00Z',
            'project_name': '项目甲',
        },
        {
            'project_code': 'B5132026Z00Z',
            'project_name': '项目乙',
        },
    ])
    manager = MatchManager(project_service=service)

    result = manager.match_project(project_code='51320262007')

    assert result['status'] == 'unmatched'
    assert result['auto_accepted'] is False


def test_ocr_zero_is_corrected_to_letter_d_when_unique():
    service = FakeProjectService([
        {
            'project_code': '18132024015D19',
            'project_name': 'expected project',
        },
        {
            'project_code': '18132024015F19',
            'project_name': 'generic one-edit neighbor',
        },
    ])
    manager = MatchManager(project_service=service)

    result = manager.match_project(
        ocr_text='',
        project_code='18132024015019',
    )

    assert result['status'] == 'matched'
    assert result['match_source'] == 'project_code_ocr_confusable'
    assert result['project_code'] == '18132024015D19'


def test_slanted_code_c_as_zero_and_z_as_two_is_corrected_when_unique():
    service = FakeProjectService([
        {
            'project_code': 'C5132025Z038',
            'project_name': 'expected project',
        },
        {
            'project_code': 'C5132025Z039',
            'project_name': 'neighbor project',
        },
    ])
    manager = MatchManager(project_service=service)

    result = manager.match_project(
        ocr_text='',
        project_code='051320252038',
    )

    assert result['status'] == 'matched'
    assert result['match_source'] == 'project_code_ocr_confusable'
    assert result['project_code'] == 'C5132025Z038'


def test_ambiguous_ocr_confusable_codes_are_not_auto_accepted():
    service = FakeProjectService([
        {'project_code': '1813202300LN', 'project_name': 'project one'},
        {'project_code': '1813202300IN', 'project_name': 'project two'},
    ])
    manager = MatchManager(project_service=service)

    result = manager.match_project(
        ocr_text='',
        project_code='18132023001N',
    )

    assert result['status'] == 'unmatched'
    assert result['auto_accepted'] is False


def test_sequence_suffix_code_overrides_misleading_name_score():
    """Printed -1 is the same business sequence as imported suffix 02."""
    misleading_name = (
        '莆田荔城黄石变10kV沙堤线泰盛凤山分线'
        '#003杆003分界开关新装业扩配套工程'
    )
    expected_name = (
        '莆田荔城黄石变10kV黄甲线东埭村#5变分线'
        '#003杆003分界开关新装业扩配套'
    )
    service = FakeProjectService([
        {
            'project_code': '18132024015F-27',
            'project_name': misleading_name,
        },
        {
            'project_code': '18132026000610',
            'project_name': '莆田荔城上庄变10kV坑园线#034A杆新装工程',
        },
        {
            'project_code': '18132026000102',
            'project_name': expected_name,
        },
    ])
    manager = MatchManager(project_service=service)

    result = manager.match_project(
        ocr_text=misleading_name,
        project_code='181320260001-1',
    )

    assert result['status'] == 'matched'
    assert result['match_source'] == 'project_code_sequence'
    assert result['project_code'] == '18132026000102'
    assert result['project_name'] == expected_name


def test_sequence_suffix_examples_are_equivalent():
    projects = [
        {'project_code': '18132026000102', 'project_name': '工程一'},
        {'project_code': '18132026000203', 'project_name': '工程二'},
        {'project_code': '18132026000304', 'project_name': '工程三'},
        {'project_code': '18132026000506', 'project_name': '工程五'},
    ]
    manager = MatchManager(project_service=FakeProjectService(projects))

    cases = (
        ('181320260001-1', '18132026000102'),
        ('181320260002-2', '18132026000203'),
        ('181320260003-3', '18132026000304'),
        ('181320260005-5', '18132026000506'),
    )

    for photographed_code, imported_code in cases:
        result = manager.match_project(
            ocr_text='',
            project_code=photographed_code,
        )
        assert result['status'] == 'matched'
        assert result['match_source'] == 'project_code_sequence'
        assert result['project_code'] == imported_code


def test_sequence_suffix_equivalence_works_in_reverse():
    service = FakeProjectService([
        {
            'project_code': '181320260001-1',
            'project_name': '工程一',
        },
    ])
    manager = MatchManager(project_service=service)

    result = manager.match_project(
        ocr_text='',
        project_code='18132026000102',
    )

    assert result['status'] == 'matched'
    assert result['match_source'] == 'project_code_sequence'
    assert result['project_code'] == '181320260001-1'


def test_sequence_suffix_rule_supports_lettered_base_codes():
    service = FakeProjectService([
        {
            'project_code': '18132024015D16',
            'project_name': '字母主码工程',
        },
    ])
    manager = MatchManager(project_service=service)

    result = manager.match_project(
        ocr_text='',
        project_code='18132024015D-15',
    )

    assert result['status'] == 'matched'
    assert result['match_source'] == 'project_code_sequence'
    assert result['project_code'] == '18132024015D16'


def test_sequence_suffix_rule_rejects_non_twelve_character_base():
    service = FakeProjectService([
        {
            'project_code': 'B1132025Z497',
            'project_name': '普通编号工程',
        },
    ])
    manager = MatchManager(project_service=service)

    result = manager.match_project(
        ocr_text='',
        project_code='B1132025Z4-96',
    )

    assert result['status'] == 'unmatched'
    assert result['auto_accepted'] is False


def test_identical_name_with_equivalent_old_and_new_codes_is_one_candidate():
    name = (
        '莆田荔城城厢变10kV城镇线双驰环网柜912开关'
        '至莆田第四中学配电室新建业扩配套工程'
    )
    service = FakeProjectService([
        {'project_code': '181320260006-8', 'project_name': name},
        {'project_code': '18132026000609', 'project_name': name},
        {'project_code': '18132024015F-19', 'project_name': '其他工程'},
    ])
    manager = MatchManager(project_service=service)

    result = manager.match_project(ocr_text=name)

    assert result['status'] == 'matched'
    assert result['auto_accepted'] is True
    assert result['project_code'] == '18132026000609'
    assert result['project_name'] == name


def test_identical_name_is_automatically_accepted():
    name = '莆田荔城220kV上庄变10kV福岭线#01杆迁改工程'
    service = FakeProjectService([
        {
            'project_code': 'P001',
            'project_name': name
        }
    ])
    manager = MatchManager(project_service=service)

    result = manager.match_project(name)

    assert result['status'] == 'matched'
    assert result['auto_accepted'] is True
    assert result['project_code'] == 'P001'
    assert result['score'] >= 82


def test_equal_top_candidates_require_manual_review():
    name = '莆田荔城220kV上庄变10kV福岭线#01杆迁改工程'
    service = FakeProjectService([
        {'project_code': 'P001', 'project_name': name},
        {'project_code': 'P002', 'project_name': name},
    ])
    manager = MatchManager(project_service=service)

    result = manager.match_project(name)

    assert result['status'] == 'uncertain'
    assert result['auto_accepted'] is False
    assert result['reason'] == 'candidate_scores_too_close'
    assert result['project_code'] == ''
    assert len(result['candidates']) == 2


def test_different_line_and_pole_are_penalized():
    strategy = PowerProjectMatchStrategy()

    detail = strategy.score(
        '莆田220kV上庄变10kV福岭线#01杆迁改工程',
        '莆田220kV上庄变10kV城龙线#05杆迁改工程'
    )

    assert detail['breakdown']['line'] < 0
    assert detail['breakdown']['pole'] < 0
    assert detail['score'] < 65


def test_photographed_start_report_is_corrected_by_excel_name():
    standard = '福建莆田荔城区坑边开闭所公变10kV重载台区治理工程'
    ocr_name = '福建靖田荔城区疯边开闭所公恋10kv重载台区治理工程'
    service = FakeProjectService([
        {
            'project_code': '1813202400START',
            'project_name': standard,
        }
    ])
    manager = MatchManager(project_service=service)

    result = manager.match_project(ocr_text=ocr_name)

    assert result['status'] == 'matched'
    assert result['auto_accepted'] is True
    assert result['project_name'] == standard
    assert result['score'] >= 76


def test_noisy_start_report_uses_named_facility_anchor():
    standard = '福建莆田荔城区坑边开闭所公变10kV重载台区治理工程'
    service = FakeProjectService([
        {
            'project_code': '18132024013H-1',
            'project_name': standard,
        },
        {
            'project_code': '1813202400YW-1',
            'project_name': (
                '福建莆田荔城区北大村#10变等'
                '10千伏重载台区治理工程'
            ),
        },
    ])
    manager = MatchManager(project_service=service)

    result = manager.match_project(
        ocr_text=(
            '一全建芋田荔城区坑边开闭所人一、'
            'zaAZEI0KVE221RTTES我台区治理工程|于各2'
        )
    )

    assert result['status'] == 'matched'
    assert result['project_code'] == '18132024013H-1'


def test_one_ocr_error_in_long_line_does_not_become_line_conflict():
    expected = (
        '莆田荔城清中变10KV清洋线洋埕港利联络线'
        '#060杆060分界开关新装业扩配网配'
    )
    service = FakeProjectService([
        {
            'project_code': '18132026000103',
            'project_name': expected,
        },
        {
            'project_code': '18132024015F-18',
            'project_name': (
                '莆田荔城供电分部2025年10kV'
                '跌落式熔断器新装业扩配套工程（二）'
            ),
        },
    ])
    manager = MatchManager(project_service=service)

    result = manager.match_project(
        ocr_text=(
            '下田妆城清中变10KV清洋线洋坦港利联络线'
            'H060杆060分春开关新装Fn业扩配网配套工程.由'
        )
    )

    assert result['status'] == 'matched'
    assert result['project_code'] == '18132026000103'
    assert result['score'] >= 76
    assert result['candidates'][0]['breakdown']['line'] > 0


def test_joined_line_segments_with_ocr_error_match_expected_project():
    expected = (
        '莆田荔城张镇变10KV尚济I路线林光辉配变分支线'
        '#001杆001分界开关新装配网'
    )
    service = FakeProjectService([
        {
            'project_code': '18132026000N09',
            'project_name': expected,
        },
        {
            'project_code': '18132024001F-15',
            'project_name': (
                '莆田荔城张镇变10KV尚济I路文献东路'
                '#1开闭所至正鼎早城充电桩电缆业扩配套工程'
            ),
        },
    ])
    manager = MatchManager(project_service=service)

    result = manager.match_project(
        ocr_text=(
            '音田荔城张镇变10KV尚济I路林光辉配恋分支线'
            '#001杆601分界开关新全“装配网业扩配套工程'
        )
    )

    assert result['status'] == 'matched'
    assert result['project_code'] == '18132026000N09'
    assert result['score'] >= 76
    assert result['candidates'][0]['breakdown']['line'] > 0


def test_primary_and_branch_lines_are_scored_separately():
    expected = (
        '莆田荔城黄石变10KV黄甲线东埭村#5变分线'
        '#003杆003分界开关新装业扩配套'
    )
    service = FakeProjectService([
        {
            'project_code': '18132026000102',
            'project_name': expected,
        },
        {
            'project_code': '18132024015F-9',
            'project_name': (
                '莆田荔城上庄变10kV院后Ⅰ路'
                '汀江村#6变新建业扩配套工程'
            ),
        },
    ])
    manager = MatchManager(project_service=service)

    result = manager.match_project(
        ocr_text=(
            '莆田荔城黄石变10kV黄甲线东雪村#变分线'
            '#003杆003分界开关新装业扩配套工程'
        )
    )

    assert result['status'] == 'matched'
    assert result['project_code'] == '18132026000102'
    assert result['candidates'][0]['breakdown']['line'] > 0


def test_batch_match_preserves_input_order_and_source():
    name = '莆田220kV上庄变10kV福岭线#01杆迁改工程'
    service = FakeProjectService([
        {'project_code': 'P001', 'project_name': name}
    ])
    manager = MatchManager(project_service=service)

    results = manager.batch_match([
        {'project_name': name},
        {'project_name': '', 'project_code': 'P001'},
    ])

    assert [item['source_index'] for item in results] == [0, 1]
    assert results[0]['status'] == 'matched'
    assert results[1]['match_source'] == 'project_code'
