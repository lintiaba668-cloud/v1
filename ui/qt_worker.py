# -*- coding: utf-8 -*-

"""Qt background worker integration.

Keeps long-running batch operations away from GUI thread.

The module gracefully handles missing Qt dependency so core modules
can still be tested in non-GUI environments.
"""

try:
    from PyQt5.QtCore import QThread, pyqtSignal
except ImportError:
    QThread = object

    class _Signal:
        def emit(self, *args, **kwargs):
            pass

        def connect(self, *args, **kwargs):
            pass

    def pyqtSignal(*args, **kwargs):
        return _Signal()


class QtWorker(QThread):

    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    log = pyqtSignal(str)

    def __init__(self, batch_worker, params=None):
        super().__init__()

        self.batch_worker = batch_worker
        self.params = params or {}
        self.result = None

    def run(self):
        try:
            self.log.emit("batch worker started")

            self.result = self.batch_worker.process_directory(
                progress_callback=self._on_progress,
                **self.params
            )

            self.finished.emit(self.result)
            self.log.emit("batch worker finished")

        except Exception as exc:
            self.error.emit(str(exc))

    def _on_progress(self, current, total, filename):
        self.progress.emit(
            current,
            total,
            filename
        )
