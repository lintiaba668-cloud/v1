# -*- coding: utf-8 -*-

"""Template-field OCR helper tests without invoking Tesseract."""

from ocr.template_field_recognizer import TemplateFieldRecognizer


def build_recognizer():
    return TemplateFieldRecognizer(executor=None)


def test_completion_title_is_classified():
    score, report_type = build_recognizer()._score_title(
        '配 网 工程 竣工 验收 报告'
    )

    assert report_type == 'finish'
    assert score >= 20


def test_start_title_is_classified_from_body_anchor():
    score, report_type = build_recognizer()._score_title(
        '配网工程开工报告 我方完成 某工程 项目开工前'
    )

    assert report_type == 'start'
    assert score >= 20


def test_body_quantity_is_not_accepted_as_project_name():
    recognizer = build_recognizer()
    candidates = recognizer._rank_names([
        '拆除工程量拆除原线路8M水泥杆1根低压电缆20米',
    ])

    assert candidates == []


def test_project_name_field_candidate_is_kept():
    recognizer = build_recognizer()
    candidates = recognizer._rank_names([
        '莆田荔城黄石变10kV黄甲线东埭村#5变分线'
        '#003杆003分界开关新装业扩配套工程',
    ])

    assert candidates
    assert candidates[0].endswith('配套工程')


def test_code_candidates_prefer_full_engineering_number():
    recognizer = build_recognizer()
    candidates = recognizer._code_candidates([
        '工程编号 18132024015F-28',
        '5028225',
    ])

    assert candidates[0] == '18132024015F-28'
