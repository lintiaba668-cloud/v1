# -*- coding: utf-8 -*-

"""Filename rule tests."""

from rename.filename_rule import FilenameRule


def test_start_report_filename():
    rule = FilenameRule()

    name = rule.build_filename(
        FilenameRule.REPORT_START,
        "测试工程"
    )

    assert name == "测试工程"


def test_completion_report_filename():
    rule = FilenameRule()

    name = rule.build_filename(
        FilenameRule.REPORT_COMPLETION,
        "测试工程",
        "ABC123-01"
    )

    assert name == "测试工程_ABC123-01"


def test_project_code_keep_hash():
    rule = FilenameRule()

    name = rule.build_filename(
        FilenameRule.REPORT_COMPLETION,
        "测试工程",
        "#035B"
    )

    assert name == "测试工程_#035B"


def test_project_code_keep_letters_numbers_dash():
    rule = FilenameRule()

    name = rule.build_filename(
        FilenameRule.REPORT_COMPLETION,
        "测试工程",
        "18132024015D-15"
    )

    assert name == "测试工程_18132024015D-15"


def test_multiline_project_name():
    rule = FilenameRule()

    name = rule.build_filename(
        FilenameRule.REPORT_START,
        "110kV变电站\n扩建工程"
    )

    assert name == "110kV变电站扩建工程"
