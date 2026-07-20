# -*- coding: utf-8 -*-

"""UI worker interface tests."""

from ui.qt_worker import QtWorker


class MockBatchWorker:

    def process_directory(self, progress_callback=None, **kwargs):
        if progress_callback:
            progress_callback(1, 1, "001.jpg")

        return {
            "total": 1,
            "success": 1,
            "failed": 0
        }


def test_qt_worker_initialization():
    worker = QtWorker(MockBatchWorker())

    assert worker.batch_worker is not None
    assert worker.params == {}


def test_qt_worker_run():
    worker = QtWorker(MockBatchWorker())
    worker.run()

    assert worker.result["success"] == 1
