"""PowerRename build prerequisite check."""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent

FILES = [
    'main.py',
    'build_win7.spec',
    'requirements.txt',
    'engine/tesseract.exe',
    'engine/tessdata/chi_sim.traineddata',
    'engine/tessdata/eng.traineddata',
]

DIRECTORIES = [
    'ocr',
    'core',
    'project',
    'ui',
]


def check():
    errors = []

    for file_name in FILES:
        if not (ROOT / file_name).exists():
            errors.append('缺少文件: ' + file_name)

    for directory in DIRECTORIES:
        if not (ROOT / directory).is_dir():
            errors.append('缺少目录: ' + directory)

    if errors:
        print('Build check failed')
        for error in errors:
            print('-', error)
        return False

    print('Build check OK')
    return True


if __name__ == '__main__':
    sys.exit(0 if check() else 1)
