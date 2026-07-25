# -*- mode: python ; coding: utf-8 -*-

"""PowerRename Win7 portable onedir build configuration."""

from pathlib import Path

block_cipher = None
base = Path('.')


def add_dir(path, target):
    if path.exists():
        return [(str(path), target)]
    return []


def add_file(path, target):
    if path.exists():
        return [(str(path), target)]
    return []


datas = []
datas += add_dir(base / 'engine', 'engine')
datas += add_dir(base / 'config', 'config')
datas += add_file(base / 'config.json', '.')
datas += add_dir(base / 'ocr' / 'dictionaries', 'ocr/dictionaries')
datas += add_file(base / 'ocr' / 'dictionary.json', 'ocr')

hiddenimports = [
    'PyQt5',
    'PyQt5.QtWidgets',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'openpyxl',
    'PIL',
    'ocr.ocr_engine',
    'ocr.ocr_executor',
    'ocr.text_parser',
    'ocr.pipeline_ocr',
    'project.project_service',
    'project.match_manager',
    'project.match_strategy',
    'rename.filename_rule',
    'rename.validator',
    'rename.batch_worker',
    'ui.main_window_v3',
    'ui.import_dialog',
    'ui.match_review_dialog',
    'core.startup_check',
    'core.final_runner',
    'core.resource',
]


a = Analysis(
    ['main.py'],
    pathex=[str(base)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'PySide6',
        'paddleocr',
        'paddlepaddle',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PowerRename',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='PowerRename',
)
