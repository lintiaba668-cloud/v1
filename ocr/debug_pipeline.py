# -*- coding: utf-8 -*-

"""OCR pipeline debug helper.

Stores intermediate images during OCR optimization.
Useful for analyzing photographed engineering documents.
"""

from pathlib import Path
import shutil
import datetime


class OCRDebugPipeline:

    def __init__(self, enabled=False, root_dir='logs/ocr_debug'):
        self.enabled = enabled
        self.root_dir = Path(root_dir)
        self.session_dir = None

    def start(self):
        if not self.enabled:
            return None

        name = datetime.datetime.now().strftime(
            '%Y%m%d_%H%M%S'
        )

        self.session_dir = self.root_dir / name
        self.session_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        return self.session_dir

    def save_image(self, name, source):
        if not self.enabled or not self.session_dir:
            return

        target = self.session_dir / name

        shutil.copy2(
            source,
            target
        )

    def save_text(self, name, content):
        if not self.enabled or not self.session_dir:
            return

        target = self.session_dir / name

        target.write_text(
            content,
            encoding='utf-8'
        )
