"""
PowerRename执行器
负责批量执行处理任务
"""

from pathlib import Path

from .pipeline import RenamePipeline


class Executor:
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.pipeline = RenamePipeline(output_dir)

    def run(self, files):
        results = []

        for file in files:
            results.append({
                'file': str(file),
                'status': '等待OCR'
            })

        return results
