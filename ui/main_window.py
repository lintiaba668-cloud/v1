# -*- coding: utf-8 -*-
"""Compatibility entry for the final PyQt5 main window."""

from ui.main_window_v3 import MainWindowV3


SUPPORTED = {
    '.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.zip'
}


class MainWindow(MainWindowV3):
    """Backward-compatible class name used by older tests and imports."""

    def __init__(self, project_service=None):
        super().__init__()
        self.worker = None

        if project_service is not None:
            self.runner.processor.service.project_service = project_service

    def attach_worker(self, worker):
        self.worker = worker

    def update_progress(self, current, total, filename):
        if total:
            self.progress.setRange(0, 100)
            self.progress.setValue(int(current * 100 / total))
        self.status_label.setText(str(filename))

    def append_log(self, message):
        self._append_log(message)
