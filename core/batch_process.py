"""
批量OCR重命名处理
"""

from core.ocr_rename_service import OCRRenameService


class BatchProcessor:
    def __init__(self, output_dir):
        self.service = OCRRenameService(output_dir)

    def run(self, files):
        results = []

        for file in files:
            results.append(self.service.process(file))

        return results
