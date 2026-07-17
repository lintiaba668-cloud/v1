# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

block_cipher = None

base = Path('.')

added_files = []

engine = base / 'engine'
if engine.exists():
    added_files.append((str(engine), 'engine'))


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'PyQt5',
        'openpyxl',
        'PIL'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
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
