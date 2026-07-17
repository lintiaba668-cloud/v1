"""
处理报告统计
"""


class ProcessReport:
    def __init__(self):
        self.success = 0
        self.failed = 0

    def add(self, status):
        if status == 'success':
            self.success += 1
        else:
            self.failed += 1

    def summary(self):
        return {
            'success': self.success,
            'failed': self.failed
        }
