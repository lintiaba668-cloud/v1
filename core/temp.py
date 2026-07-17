"""
临时目录管理
"""

from pathlib import Path
import tempfile


def create_temp_dir():
    return Path(tempfile.mkdtemp(prefix='PowerRename_'))
