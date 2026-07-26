# -*- coding: utf-8 -*-
"""Safe cleanup for PowerRename-generated runtime cache."""

import os
import shutil
from pathlib import Path

from core.resource import get_base_path


CACHE_DIRECTORIES = (
    Path('logs') / 'template_ocr',
    Path('temp') / 'imported',
)


def clear_runtime_cache(base_path=None, protected_paths=None):
    """Clear only known generated cache directories.

    Active ZIP-extracted files can be supplied as protected paths. A cache
    directory containing one of those files is skipped in full so the current
    import list never points to a deleted image.
    """
    base = Path(base_path or get_base_path()).resolve()
    protected = [
        Path(value).resolve()
        for value in (protected_paths or [])
    ]
    summary = {
        'files_removed': 0,
        'bytes_removed': 0,
        'directories_cleared': 0,
        'skipped': [],
    }

    for relative in CACHE_DIRECTORIES:
        target = (base / relative).resolve()
        if not _is_inside(target, base) or target == base:
            raise ValueError('缓存目录超出程序目录: ' + str(target))

        if any(_is_inside(value, target) for value in protected):
            summary['skipped'].append(str(target))
            continue

        if not target.exists():
            continue

        for child in list(target.iterdir()):
            file_count, byte_count = _measure(child)
            if child.is_dir():
                shutil.rmtree(str(child))
            else:
                child.unlink()
            summary['files_removed'] += file_count
            summary['bytes_removed'] += byte_count

        summary['directories_cleared'] += 1

    return summary


def _measure(path):
    if path.is_file():
        try:
            return 1, path.stat().st_size
        except OSError:
            return 1, 0

    count = 0
    size = 0
    for item in path.rglob('*'):
        if not item.is_file():
            continue
        count += 1
        try:
            size += item.stat().st_size
        except OSError:
            pass
    return count, size


def _is_inside(path, parent):
    try:
        return os.path.normcase(os.path.commonpath([
            str(path),
            str(parent),
        ])) == os.path.normcase(str(parent))
    except ValueError:
        return False
