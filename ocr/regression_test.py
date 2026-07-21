# -*- coding: utf-8 -*-

"""OCR regression test runner.

Used to verify field extraction after OCR pipeline changes.
"""

import json
from pathlib import Path

from .ocr_engine import OCREngine


EXPECTED = {
    'project_code': '181320260001-7'
}


class OCRRegressionTest:

    def __init__(self):
        self.engine = OCREngine()

    def run(self, image_path):
        result = self.engine.recognize(image_path)

        report = {
            'image': str(image_path),
            'project_name': result.get('project_name', ''),
            'project_code': result.get('project_code', ''),
            'passed': self.check(result)
        }

        output = Path('logs/ocr_test/regression_result.json')
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        return report

    def check(self, result):
        code = result.get('project_code', '')
        return code == EXPECTED['project_code']
