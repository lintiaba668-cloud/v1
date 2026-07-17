"""
GUI控制层
连接界面与处理流程
"""

from pathlib import Path

from core.workflow import Workflow


class AppController:
    def __init__(self):
        self.workflow = None
        self.output_dir = Path('output')

    def load_file(self, path):
        self.workflow = Workflow(self.output_dir)
        count = self.workflow.add(path)
        return count

    def start(self):
        if self.workflow:
            return self.workflow.run()
        return []
