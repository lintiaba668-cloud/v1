# -*- coding: utf-8 -*-

"""Tesseract OCR执行层.

负责：
- tesseract调用
- 超时处理
- 错误处理
- 临时文件生命周期

不负责：
- TSV解析
- 工程字段提取
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

        temp_file = None

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as file:
                temp_file = file.name

            env = os.environ.copy()
            env["TESSDATA_PREFIX"] = str(self.tessdata)

            command = [
                str(self.ocr_exe),
                str(image_path),
                temp_file,
                "-l",
                "chi_sim+eng",
                "tsv"
            ]

            result = subprocess.run(
                command,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout
            )

            if result.returncode != 0:
                return self._failed(
                    ErrorCode.OCR_EXEC_FAILED,
                    result.stderr.decode("utf-8", errors="ignore")
                )

            return {
                "success": True,
                "tsv_file": Path(temp_file + ".tsv"),
                "temp_file": Path(temp_file),
                "error_code": ErrorCode.SUCCESS,
                "error_message": ""
            }

        except subprocess.TimeoutExpired:
            return self._failed(ErrorCode.OCR_TIMEOUT, "OCR execution timeout")

        except Exception as exc:
            logger.exception("OCR executor exception")
            return self._failed(ErrorCode.OCR_EXEC_FAILED, str(exc))

        finally:
            if temp_file:
                path = Path(temp_file)
                if path.exists():
                    path.unlink()

    def cleanup(self, result):
        """由调用方完成TSV解析后调用。"""
        if not result:
            return

        tsv_file = result.get("tsv_file")
        if tsv_file and Path(tsv_file).exists():
            Path(tsv_file).unlink()

    def _failed(self, code, message):
        logger.error("[%s] %s", code, message)
        return {
            "success": False,
            "tsv_file": None,
            "error_code": code,
            "error_message": message
        }
