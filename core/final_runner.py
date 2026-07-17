"""
V1最终运行入口
"""

from pathlib import Path

from core.batch_process import BatchProcessor
from core.excel_result_writer import ExcelResultWriter


class FinalRunner:
    def __init__(self, output_dir='output'):
        self.output_dir = Path(output_dir)
        self.processor = BatchProcessor(output_dir)
        self.excel = ExcelResultWriter()

    def run(self, files):
        results = self.processor.run(files)

        for result in results:
            self.excel.add(result)

        self.excel.save(self.output_dir / '重命名记录.xlsx')

        return results
