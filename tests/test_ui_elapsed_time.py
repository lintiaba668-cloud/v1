# -*- coding: utf-8 -*-

"""Elapsed-time display formatting tests."""

from ui import main_window_v3
from ui.main_window_v3 import format_elapsed_time


def test_elapsed_time_formats_minutes_and_seconds():
    assert format_elapsed_time(0) == '00:00'
    assert format_elapsed_time(65.9) == '01:05'


def test_elapsed_time_includes_hours_for_long_batches():
    assert format_elapsed_time(3661) == '01:01:01'


def test_elapsed_timer_updates_label_and_stops(monkeypatch):
    moments = iter((100.0, 165.9, 166.2))

    class FakeLabel:

        def __init__(self):
            self.text = ''

        def setText(self, value):
            self.text = value

    class FakeTimer:

        def __init__(self):
            self.running = False

        def start(self):
            self.running = True

        def stop(self):
            self.running = False

    class FakeWindow:
        _batch_started_at = None
        _elapsed_seconds = 0.0
        elapsed_label = FakeLabel()
        elapsed_timer = FakeTimer()

        _update_elapsed_time = (
            main_window_v3.MainWindowV3._update_elapsed_time
        )

    window = FakeWindow()
    monkeypatch.setattr(
        main_window_v3.time,
        'monotonic',
        lambda: next(moments),
    )

    main_window_v3.MainWindowV3._start_elapsed_time(window)
    window._update_elapsed_time()

    assert window.elapsed_timer.running is True
    assert window.elapsed_label.text == '运行时间：01:05'

    main_window_v3.MainWindowV3._stop_elapsed_time(window)

    assert window.elapsed_timer.running is False
    assert window.elapsed_label.text == '运行时间：01:06'
