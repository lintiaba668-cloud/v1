"""
任务处理管理
"""

from pathlib import Path

from .scanner import scan_images


class TaskManager:
    def __init__(self):
        self.files = []

    def add_path(self, path):
        self.files.extend(scan_images(path))

    def count(self):
        return len(self.files)

    def clear(self):
        self.files.clear()
