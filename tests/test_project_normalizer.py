# -*- coding: utf-8 -*-

from project.normalizer import ProjectNormalizer


def test_normalization_is_idempotent_for_number_markers():
    normalizer = ProjectNormalizer()
    value = '莆田荔城栏山#4变支线#01杆迁改工程'

    once = normalizer.normalize(value)
    twice = normalizer.normalize(once)

    assert once == twice
    assert '##' not in once


def test_common_voltage_ocr_errors_are_normalized():
    normalizer = ProjectNormalizer()

    assert '10kV' in normalizer.normalize('城东变10kY岳公线')
    assert '10kV' in normalizer.normalize('坑边开闭所0kV台区治理')
