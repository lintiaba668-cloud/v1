"""
处理状态管理
"""


class ProcessState:
    def __init__(self):
        self.total = 0
        self.current = 0
        self.status = '等待'

    def update(self, current, total):
        self.current = current
        self.total = total

    def percent(self):
        if self.total == 0:
            return 0
        return int(self.current / self.total * 100)
