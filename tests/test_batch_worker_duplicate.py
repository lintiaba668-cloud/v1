# -*- coding: utf-8 -*-

"""Batch worker duplicate filename tests."""

from pathlib import Path

from rename.batch_worker import BatchWorker


def test_unique_target(tmp_path):
    worker = BatchWorker(None, None, None)

    first = tmp_path / "工程.jpg"
    first.write_text("1", encoding="utf-8")

    target = worker._unique_target(
        tmp_path,
        "工程",
        ".jpg"
    )

    assert target.name == "工程(1).jpg"
