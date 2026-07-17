"""
OCR失败重试机制
"""


class RetryPolicy:
    def __init__(self, times=2):
        self.times = times

    def should_retry(self, count):
        return count < self.times
