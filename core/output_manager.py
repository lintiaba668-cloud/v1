"""
输出目录管理
"""

from pathlib import Path


class OutputManager:
    def __init__(self, root='output'):
        self.root = Path(root)
        self.images = self.root / '已重命名图片'
        self.failed = self.root / '未识别'

    def prepare(self):
        self.images.mkdir(parents=True, exist_ok=True)
        self.failed.mkdir(parents=True, exist_ok=True)

    def paths(self):
        return {
            'images': self.images,
            'failed': self.failed
        }
