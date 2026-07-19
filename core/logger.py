"""
PowerRename 日志管理模块

职责：
1. 统一应用日志输出；
2. 支持源码运行和PyInstaller绿色版运行；
3. 避免业务模块直接管理日志文件。
"""

import logging
import sys
from pathlib import Path

from core.resource import get_resource_path


_LOGGER_NAME = "PowerRename"


class AppLogger:

    @staticmethod
    def get_base_dir() -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parent.parent

    @classmethod
    def setup(cls, level=logging.INFO):
        logger = logging.getLogger(_LOGGER_NAME)

        if logger.handlers:
            return logger

        logger.setLevel(level)

        log_dir = get_resource_path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / "PowerRename.log"

        handler = logging.FileHandler(
            log_file,
            encoding="utf-8"
        )

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger


def init_logger():
    return AppLogger.setup()


def get_logger(module):
    return logging.getLogger(
        f"{_LOGGER_NAME}.{module}"
    )


logger = AppLogger.setup()
