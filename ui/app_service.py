"""
应用服务层
统一管理加载、处理、状态回调
"""

from pathlib import Path

from core.workflow import Workflow


class AppService:
    def __init__(self, output_dir='output'):
        self.output_dir = Path(output_dir)
        self.workflow = Workflow(self.output_dir)

    def load(self, path):
        count = self.workflow.add(path)
        return {
            'count': count,
            'message': f'已加载 {count} 张图片'
        }

    def run(self):
        return self.workflow.run()
