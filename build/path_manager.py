# -*- coding: utf-8 -*-
"""
Runtime path manager for portable version.
"""

import sys
from pathlib import Path


class PathManager:

    @staticmethod
    def root_path():
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent

        return Path(__file__).resolve().parent.parent

    @classmethod
    def data_path(cls):
        path = cls.root_path() / 'data'
        path.mkdir(exist_ok=True)
        return path

    @classmethod
    def model_path(cls):
        return cls.root_path() / 'models'

    @classmethod
    def backup_path(cls):
        path = cls.root_path() / 'backup'
        path.mkdir(exist_ok=True)
        return path
