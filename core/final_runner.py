"""V1 final batch runner."""

from pathlib import Path

from core.batch_process import BatchProcessor
from core.excel_result_writer import ExcelResultWriter
from core.resource import get_resource_path


class FinalRunner:
    def __init__(self, output_dir=None):
        if output_dir is None:
            output_dir = get_resource_path('output')

        self.output_dir = Path(output_dir)
        self.processor = BatchProcessor(self.output_dir)
        self.excel = ExcelResultWriter()

    def run(
        self,
        files,
        progress_callback=None,
        stage_callback=None,
    ):
        results = self.processor.run(
            files,
            progress_callback=progress_callback,
            stage_callback=stage_callback,
        )
        self.save_results(results)
        return results

    def save_results(self, results):
        """Rewrite the result workbook from the supplied authoritative list."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.excel = ExcelResultWriter()

        for result in results:
            self.excel.add(result)

        target = self.output_dir / '重命名记录.xlsx'
        self.excel.save(target)
        return target
