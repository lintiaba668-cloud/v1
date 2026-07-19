"""
PowerRename 日志管理模块

职责：
1. 统一应用日志输出；
2. 支持源码运行和EXE绿色版运行；
3. 避免UI、OCR模块直接操作日志文件。
"""

import logging
import sys
from pathlib import Path


_LOGGER_NAME = "PowerRename"


class AppLogger:
    """应用日志初始化管理"""

    @staticmethod
    def get_base_dir() -> Path:
        """获取程序根目录，兼容PyInstaller EXE。"""
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parent.parent

    @classmethod
    def setup(cls) -> logging.Logger:
        logger = logging.getLogger(_LOGGER_NAME)

        if logger.handlers:
            return logger

        logger.setLevel(logging.INFO)

        log_dir = cls.get_base_dir() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(
            log_dir / "app.log",
            encoding="utf-8"
        )

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )

        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger


logger = AppLogger.setup()
