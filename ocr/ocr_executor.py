# -*- coding: utf-8 -*-

"""Tesseract OCR执行层.

负责：
- tesseract调用
- TSV坐标输出
- 超时处理
- 错误处理
- 临时文件生命周期
"""

import logging
import os
import subprocess
import tempfile
from pathlib import Path

from core.error_code import ErrorCode
from core.resource import get_resource_path

logger = logging.getLogger("PowerRename.OCRExecutor")


class OCRExecutor:

    def __init__(self, timeout=60):
        self.timeout = timeout
        self.ocr_exe = get_resource_path("engine/tesseract.exe")
        self.tessdata = get_resource_path("engine/tessdata")

    def execute(self, image_path):
        if not self.ocr_exe.exists():
            return self._failed(ErrorCode.ENGINE_MISSING, "OCR engine missing")

        try:
            output_base = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=""
            ).name

            env = os.environ.copy()
            env["TESSDATA_PREFIX"] = str(self.tessdata)

            command = [
                str(self.ocr_exe),
                str(image_path),
                output_base,
                "--psm",
                "6",
                "-l",
                "chi_sim+eng",
                "tsv"
            ]

            logger.info('[OCR] execute image=%s', image_path)
            logger.info('[OCR_CMD] %s', ' '.join(command))

            result = subprocess.run(
                command,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout
            )

            stderr = result.stderr.decode(
                "utf-8",
                errors="ignore"
            )

            if result.returncode != 0:
                return self._failed(
                    ErrorCode.OCR_EXEC_FAILED,
                    stderr
                )

            tsv_path = Path(output_base + ".tsv")

            size = tsv_path.stat().st_size if tsv_path.exists() else 0

            logger.info(
                '[OCR_DATA] tsv=%s exists=%s size=%s',
                tsv_path,
                tsv_path.exists(),
                size
            )

            return {
                "success": True,
                "tsv_file": tsv_path,
                "temp_file": Path(output_base),
                "error_code": ErrorCode.SUCCESS,
                "error_message": ""
            }

        except subprocess.TimeoutExpired:
            return self._failed(ErrorCode.OCR_TIMEOUT, "OCR execution timeout")
        except Exception as exc:
            logger.exception("OCR executor exception")
            return self._failed(ErrorCode.OCR_EXEC_FAILED, str(exc))

    def cleanup(self, result):
        if not result:
            return

        for key in ("tsv_file", "temp_file"):
            file_path = result.get(key)
            if file_path:
                path = Path(file_path)
                try:
                    if path.exists():
                        path.unlink()
                except Exception:
                    logger.warning("cleanup failed: %s", path)

    def _failed(self, code, message):
        logger.error("[%s] %s", code, message)
        return {
            "success": False,
            "tsv_file": None,
            "temp_file": None,
            "error_code": code,
            "error_message": message
        }
