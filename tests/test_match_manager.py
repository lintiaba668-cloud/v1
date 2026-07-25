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
