# -*- coding: utf-8 -*-

"""Main window tests."""

import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt5.QtWidgets import QApplication

from ui.main_window import MainWindow


def get_app():
    return QApplication.instance() or QApplication([])


def test_main_window_init():
    app = get_app()
    window = MainWindow()

    assert app is not None
    assert window.worker is None
    assert window.windowTitle() != ''
    assert window.centralWidget() is not None

    window.close()


def test_supported_types():
    from ui.main_window import SUPPORTED

    assert '.jpg' in SUPPORTED
    assert '.zip' in SUPPORTED
    assert '.tiff' in SUPPORTED
