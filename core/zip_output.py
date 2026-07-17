"""
输出ZIP打包模块
"""

from pathlib import Path
import zipfile


def make_zip(folder, output_file):
    folder = Path(folder)

    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as z:
        for file in folder.rglob('*'):
            if file.is_file():
                z.write(file, file.relative_to(folder))

    return output_file
