"""
未识别文件管理
"""

from pathlib import Path


class UnrecognizedManager:
    def __init__(self, folder='未识别'):
        self.folder = Path(folder)
        self.items = []

    def add(self, file, reason='无法识别工程信息'):
        self.items.append({
            'file': str(file),
            'reason': reason
        })

    def count(self):
        return len(self.items)
