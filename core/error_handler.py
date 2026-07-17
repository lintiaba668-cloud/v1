"""
错误处理模块
"""


class ProcessError:
    def __init__(self, file='', reason=''):
        self.file = file
        self.reason = reason

    def to_dict(self):
        return {
            'file': self.file,
            'reason': self.reason
        }


def create_error(file, reason):
    return ProcessError(file, reason)
