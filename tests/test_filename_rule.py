# -*- coding: utf-8 -*-

"""Filename rule tests."""

from rename.filename_rule import FilenameRule


def test_start_report_filename():
    rule = FilenameRule()

    name = rule.build_filename(
        "start",
        "测试工程"
    )

    assert name == "测试工程"


def test_completion_report_filename():
    rule = FilenameRule()

    name = rule.build_filename(
        "completion",
        "测试工程",
        "ABC123-01"
    )

    assert name == "测试工程_ABC123-01"
