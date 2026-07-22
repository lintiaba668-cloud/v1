# -*- coding: utf-8 -*-

"""
Power matcher tests.
"""

from project.power_matcher import PowerProjectMatcher


def test_power_project_match_case():
    matcher = PowerProjectMatcher()

    ocr_name = (
        '莆田荔城220kV土庄变10kV湖峰线兰山4变支线401杆迁改工程'
    )

    standard_name = (
        '莆田荔城220kV上庄变10kV福岭线栏山#4变支线#01杆迁改工程'
    )

    score = matcher.score(
        ocr_name,
        standard_name
    )

    assert score >= 60


def test_different_pole_should_not_high_score():
    matcher = PowerProjectMatcher()

    score = matcher.score(
        '莆田220kV上庄变10kV福岭线栏山#01杆迁改工程',
        '莆田220kV上庄变10kV福岭线栏山#05杆迁改工程'
    )

    assert score < 100
