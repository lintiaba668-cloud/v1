# -*- coding: utf-8 -*-

"""Project-library cache tests."""

from project.project_service import ProjectService


def _project(code, name):
    return {
        'project_code': code,
        'project_name': name,
        'normalized_name': name,
    }


def test_project_library_is_loaded_once_for_list_and_code_lookup(
    tmp_path,
    monkeypatch,
):
    service = ProjectService(tmp_path / 'projects.db')
    service.commit_import([_project('CODE-1', 'Project One')])
    original = service.db.list_all
    calls = []

    def counted_list_all():
        calls.append(True)
        return original()

    monkeypatch.setattr(service.db, 'list_all', counted_list_all)

    assert service.list_projects()[0]['project_code'] == 'CODE-1'
    assert service.list_projects()[0]['project_code'] == 'CODE-1'
    assert service.find_by_code('CODE-1')['project_name'] == 'Project One'
    assert len(calls) == 1


def test_project_library_cache_is_invalidated_after_import(
    tmp_path,
    monkeypatch,
):
    service = ProjectService(tmp_path / 'projects.db')
    service.commit_import([_project('CODE-1', 'Project One')])
    original = service.db.list_all
    calls = []

    def counted_list_all():
        calls.append(True)
        return original()

    monkeypatch.setattr(service.db, 'list_all', counted_list_all)

    assert len(service.list_projects()) == 1
    service.commit_import([_project('CODE-2', 'Project Two')])

    assert len(service.list_projects()) == 2
    assert service.find_by_code('CODE-2')['project_name'] == 'Project Two'
    assert len(calls) == 2
