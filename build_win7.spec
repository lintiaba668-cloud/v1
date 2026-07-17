# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

block_cipher = None

base = Path('.')


def add_dir(path, target):
    if path.exists():
        return [(str(path), target)]
    return []


datas = []
datas += add_dir(base / 'engine', 'engine')
datas += add_dir(base / 'config', 'config')

hiddenimports = [
    'PyQt5',
    'PyQt5.QtWidgets',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'openpyxl',
    'PIL',
    'ocr.ocr_engine',
    'ocr.pipeline_ocr',
    'ocr.field_region_v28',
    'ocr.text_parser',
    'core.startup_check',
    'core.final_runner'
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
        'paddleocr',
        'paddlepaddle'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='PowerRename',
    debug=False,
    strip=False,
    upx=False,
    console=False
)
