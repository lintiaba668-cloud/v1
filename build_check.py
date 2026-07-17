"""
PowerRename 打包前检查
检查PyInstaller发布所需文件
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parent


FILES = [
    'main.py',
    'build_win7.spec',
    'requirements.txt'
]


def check():
    errors = []

    for file in FILES:
        if not (ROOT / file).exists():
            errors.append(f'缺少文件:{file}')

    if not (ROOT / 'ocr').exists():
        errors.append('缺少ocr目录')

    if not (ROOT / 'core').exists():
        errors.append('缺少core目录')

    if errors:
        print('Build check failed')
        for e in errors:
            print('-', e)
    else:
        print('Build check OK')


if __name__ == '__main__':
    check()
