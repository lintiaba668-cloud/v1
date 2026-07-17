"""
PowerRename V1
电力工程开竣工报告批量重命名工具

第一阶段：项目入口
"""

from pathlib import Path

SUPPORTED_EXT = {
    '.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'
}


def scan_files(folder):
    """扫描图片文件"""
    files = []
    for p in Path(folder).rglob('*'):
        if p.suffix.lower() in SUPPORTED_EXT:
            files.append(p)
    return files


if __name__ == '__main__':
    print('PowerRename V1 启动')
