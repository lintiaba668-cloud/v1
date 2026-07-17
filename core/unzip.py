"""
ZIP解压模块
"""

from pathlib import Path
import zipfile


def extract_zip(zip_path, output_dir):
    """解压ZIP文件"""
    zip_path = Path(zip_path)
    output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(output_dir)

    return output_dir
