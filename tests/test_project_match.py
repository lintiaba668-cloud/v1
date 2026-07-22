# -*- coding: utf-8 -*-

"""
Project matching tests.

Verify OCR project names can be matched against imported project data.
"""

from project.matcher import ProjectMatcher


def test_power_project_name_similarity():
    matcher = ProjectMatcher()

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

    assert score > 75
