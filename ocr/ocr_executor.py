# -*- coding: utf-8 -*-

"""
Tesseract OCR执行层

职责：
1. 管理内置tesseract调用；
2. 处理timeout、returncode、stderr；
3. 管理OCR临时文件。

不负责：
- TSV解析；
- 工程名称提取；
- 文件命名规则。
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
        self.ocr_exe = get_resource_path(
            "engine/tesseract.exe"
        )
        self.tessdata = get_resource_path(
            "engine/tessdata"
        )

    def execute(self, image_path):

        if not self.ocr_exe.exists():
            return self._failed(
                ErrorCode.ENGINE_MISSING,
                "OCR engine missing"
            )

        temp_file = None

        try:
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".txt"
            ) as f:
                temp_file = f.name

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

            logger.info(
                "execute OCR: %s",
                image_path
            )

            result = subprocess.run(
                command,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout
            )

            if result.returncode != 0:
                stderr = result.stderr.decode(
                    "utf-8",
                    errors="ignore"
                )

                return self._failed(
                    ErrorCode.OCR_EXEC_FAILED,
                    stderr
                )

            return {
                "success": True,
                "tsv_file": Path(temp_file + ".tsv"),
                "error_code": ErrorCode.SUCCESS,
                "error_message": ""
            }

        except subprocess.TimeoutExpired:
            return self._failed(
                ErrorCode.OCR_TIMEOUT,
                "OCR execution timeout"
            )

        except Exception as exc:
            logger.exception(
                "OCR executor exception"
            )
            return self._failed(
                ErrorCode.OCR_EXEC_FAILED,
                str(exc)
            )

        finally:
            self._remove_temp(temp_file)

    def _remove_temp(self, temp_file):
        if not temp_file:
            return

        for path in [
            Path(temp_file),
            Path(temp_file + ".tsv")
        ]:
            try:
                if path.exists():
                    path.unlink()
            except Exception:
                logger.warning(
                    "remove temp failed: %s",
                    path
                )

    def _failed(self, code, message):
        logger.error(
            "[%s] %s",
            code,
            message
        )

        return {
            "success": False,
            "tsv_file": None,
            "error_code": code,
            "error_message": message
        }
