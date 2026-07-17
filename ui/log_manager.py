"""
GUI日志管理
"""

from datetime import datetime


class LogManager:
    def __init__(self):
        self.logs = []

    def add(self, message):
        text = f'[{datetime.now().strftime("%H:%M:%S")}] {message}'
        self.logs.append(text)
        return text

    def all(self):
        return '\n'.join(self.logs)
