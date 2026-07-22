# -*- coding: utf-8 -*-

"""
Dataset driven project matching tests.

Load project matching cases from JSON and validate matcher behavior.
"""

import json
from pathlib import Path

from project.power_matcher import PowerProjectMatcher


DATA_FILE = Path(__file__).parent / 'data' / 'project_match_cases.json'


def load_cases():
    with open(DATA_FILE, 'r', encoding='utf-8') as file:
        return json.load(file)


def test_dataset_matching():
    matcher = PowerProjectMatcher()

    for case in load_cases():
        score = matcher.score(
            case['ocr'],
            case['standard']
        )

        if case['expect_match']:
            assert score >= 60, (
                case['name'] + ' score=' + str(score)
            )
        else:
            assert score < 60, (
                case['name'] + ' score=' + str(score)
            )
