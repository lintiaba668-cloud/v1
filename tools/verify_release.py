# -*- coding: utf-8 -*-

"""PowerRename release package verifier.

Checks whether a green release directory contains required resources.
"""

import sys
from pathlib import Path


REQUIRED_FILES = [
    "PowerRename.exe",
    "engine/tesseract.exe",
    "engine/tessdata/chi_sim.traineddata",
    "engine/tessdata/eng.traineddata",
    "config/config.json"
]

REQUIRED_DIRS = [
    "engine",
    "engine/tessdata",
    "config",
    "output",
    "logs"
]


def verify_release(root):
    root = Path(root)
    errors = []

    for item in REQUIRED_FILES:
        if not (root / item).exists():
            errors.append(
                "missing file: " + item
            )

    for item in REQUIRED_DIRS:
        if not (root / item).is_dir():
            errors.append(
                "missing directory: " + item
            )

    return errors


def main():
    if len(sys.argv) < 2:
        print("Usage: verify_release.py <release_dir>")
        return 1

    errors = verify_release(sys.argv[1])

    if errors:
        print("RELEASE CHECK FAILED")
        for error in errors:
            print(error)
        return 1

    print("RELEASE CHECK PASS")
    return 0


if __name__ == '__main__':
    sys.exit(main())
