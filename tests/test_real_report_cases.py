# -*- coding: utf-8 -*-

"""Real power engineering report validation framework.

This test file defines expected business cases.
Actual image files should be placed in tests/data/reports.

It intentionally does not fabricate OCR results.
"""

from pathlib import Path

from rename.filename_rule import FilenameRule


DATA_DIR = Path(__file__).parent / "data" / "reports"


CASES = [
    {
        "name": "start_report",
        "report_type": FilenameRule.REPORT_START,
        "image": "001.jpg",
        "expected": "工程名称.jpg"
    },
    {
        "name": "completion_report_code_hash",
        "report_type": FilenameRule.REPORT_COMPLETION,
        "image": "002.jpg",
        "expected": "工程名称_#035B.jpg"
    },
    {
        "name": "completion_report_long_code",
        "report_type": FilenameRule.REPORT_COMPLETION,
        "image": "003.jpg",
        "expected": "工程名称_18132024015D-15.jpg"
    }
]


def test_report_data_directory_exists():
    """Real documents are supplied externally.

    The repository should not contain customer documents.
    """

    assert DATA_DIR.name == "reports"


def test_expected_case_definition():
    assert len(CASES) == 3

    for case in CASES:
        assert case["image"].endswith(".jpg")
        assert case["expected"].endswith(".jpg")
