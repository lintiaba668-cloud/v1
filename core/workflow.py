"""
PowerRename完整工作流
"""

from pathlib import Path

from .file_input import FileInput
from .executor import Executor


class Workflow:
    def __init__(self, output_dir):
        self.input = FileInput()
        self.executor = Executor(output_dir)
        self.files = []

    def add(self, path):
        self.files = self.input.load(path)
        return len(self.files)

    def run(self):
        return self.executor.run(self.files)
