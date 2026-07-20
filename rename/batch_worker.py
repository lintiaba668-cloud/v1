# -*- coding: utf-8 -*-

"""Batch rename processing worker.

Pipeline:
image
 -> OCR
 -> filename rule
 -> validator
 -> output

This module does not depend on UI thread.
"""

from pathlib import Path
import shutil


class BatchWorker:

    IMAGE_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp"
    }

    def __init__(
        self,
        ocr_engine,
        filename_rule,
        validator
    ):
        self.ocr_engine = ocr_engine
        self.filename_rule = filename_rule
        self.validator = validator

    def process_directory(
        self,
        input_dir,
        output_dir,
        report_type,
        progress_callback=None
    ):
        stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "errors": []
        }

        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        images = self._scan_images(input_path)
        stats["total"] = len(images)

        for index, image in enumerate(images, start=1):
            try:
                result = self.ocr_engine.recognize(image)

                filename = self.filename_rule.build_filename(
                    report_type,
                    result.get("project_name", ""),
                    result.get("project_code", "")
                )

                valid, message = self.validator.validate(filename)

                if not valid:
                    raise ValueError(message)

                target = self._unique_target(
                    output_path,
                    filename,
                    image.suffix
                )

                shutil.copy2(image, target)
                stats["success"] += 1

            except Exception as exc:
                stats["failed"] += 1
                stats["errors"].append({
                    "file": str(image),
                    "message": str(exc)
                })

            finally:
                if progress_callback:
                    progress_callback(
                        index,
                        stats["total"],
                        str(image)
                    )

        return stats

    def _unique_target(self, directory, filename, suffix):
        target = directory / (filename + suffix)

        if not target.exists():
            return target

        index = 1

        while True:
            target = directory / (
                "%s(%d)%s" % (
                    filename,
                    index,
                    suffix
                )
            )

            if not target.exists():
                return target

            index += 1

    def _scan_images(self, directory):
        if not directory.exists():
            return []

        return [
            item
            for item in directory.iterdir()
            if item.is_file()
            and item.suffix.lower()
            in self.IMAGE_EXTENSIONS
        ]
