# -*- coding: utf-8 -*-

"""Main-window batch progress presentation tests."""

from ui import main_window_v3


class FakeProgress:

    def __init__(self):
        self.range = None
        self.value = None

    def setRange(self, minimum, maximum):
        self.range = (minimum, maximum)

    def setValue(self, value):
        self.value = value


class FakeLabel:

    def __init__(self):
        self.text = ''

    def setText(self, value):
        self.text = value


class FakeItem:

    def __init__(self, text):
        self._text = text
        self.background = None

    def text(self):
        return self._text

    def setBackground(self, background):
        self.background = background


class FakeList:

    def __init__(self, values):
        self.items = [FakeItem(value) for value in values]

    def count(self):
        return len(self.items)

    def item(self, index):
        return self.items[index]


def test_progress_updates_percentage_and_highlights_completed_file():
    class FakeWindow:
        progress = FakeProgress()
        progress_percent_label = FakeLabel()
        status_label = FakeLabel()
        file_list = FakeList(('first.jpg', 'second.jpg', 'third.jpg'))

        _update_file_counts = (
            main_window_v3.MainWindowV3._update_file_counts
        )
        _mark_file_processed = (
            main_window_v3.MainWindowV3._mark_file_processed
        )

    window = FakeWindow()

    main_window_v3.MainWindowV3.on_progress(
        window,
        1,
        3,
        'second.jpg',
    )

    assert window.progress.range == (0, 100)
    assert window.progress.value == 33
    assert window.progress_percent_label.text == '33%'
    assert window.status_label.text == '待处理文件：2    已处理：1'
    assert window.file_list.item(0).background is None
    assert (
        window.file_list.item(1).background.color().name()
        == '#cfefff'
    )
    assert window.file_list.item(2).background is None


def test_stage_progress_shows_fast_and_deep_queues():
    class FakeWindow:
        phase_label = FakeLabel()
        _difficult_count = 0

    window = FakeWindow()

    main_window_v3.MainWindowV3.on_stage_progress(
        window,
        'fast',
        8,
        10,
        2,
    )

    assert window._difficult_count == 2
    assert window.phase_label.text == (
        '识别阶段：快速识别 8/10    困难队列：2'
    )

    main_window_v3.MainWindowV3.on_stage_progress(
        window,
        'deep',
        1,
        2,
        1,
    )

    assert window.phase_label.text == (
        '识别阶段：精细识别 1/2    剩余：1'
    )
