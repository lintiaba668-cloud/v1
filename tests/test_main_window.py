# -*- coding: utf-8 -*-

"""Main window tests."""

from ui.main_window import MainWindow


def test_main_window_init():
    window = MainWindow()

    assert window.worker is None
    assert window.windowTitle() != ""


def test_supported_types():
    from ui.main_window import SUPPORTED

    assert '.jpg' in SUPPORTED
    assert '.zip' in SUPPORTED
