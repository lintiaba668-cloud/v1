"""
文件拖拽支持
"""

from pathlib import Path


class DragDropHandler:
    def __init__(self):
        self.files = []

    def accept(self, paths):
        self.files = [Path(p) for p in paths]
        return self.files
