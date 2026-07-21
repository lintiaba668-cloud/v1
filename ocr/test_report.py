# -*- coding: utf-8 -*-

"""OCR diagnostic report helper.

Used during OCR optimization to compare:
- raw OCR output
- layout reconstruction
- extracted fields
"""

from pathlib import Path
import json


class OCRTestReport:

    def __init__(self, output_dir='logs/ocr_test'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    def save(self, image_name, result):
        report = {
            'image': image_name,
            'raw_text': result.get('raw_text', ''),
            'project_name': result.get('project_name', ''),
            'project_code': result.get('project_code', ''),
            'items_count': len(result.get('items', []))
        }

        target = self.output_dir / (
            Path(image_name).stem + '_report.json'
        )

        target.write_text(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2
            ),
            encoding='utf-8'
        )

        return target
