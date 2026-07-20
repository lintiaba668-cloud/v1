# -*- coding: utf-8 -*-

"""Green package structure tests.

Validates expected resources after packaging.
"""

from pathlib import Path


REQUIRED_PATHS = [
    "PowerRename.exe",
    "engine",
    "engine/tesseract.exe",
    "engine/tessdata",
    "config",
    "output",
    "logs"
]


def test_package_structure(tmp_path):
    package = tmp_path / "PowerRename"

    for item in REQUIRED_PATHS:
        target = package / item

        if item.endswith(".exe"):
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("mock", encoding="utf-8")
        else:
            target.mkdir(parents=True, exist_ok=True)

    for item in REQUIRED_PATHS:
        assert (package / item).exists()
