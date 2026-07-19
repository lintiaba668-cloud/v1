# -*- coding: utf-8 -*-
"""
PowerRename configuration manager.

Handles config/config.json creation, loading and recovery.
"""

import json

from core.resource import get_resource_path


class ConfigManager:

    DEFAULT_CONFIG = {
        "ocr_path": "engine/tesseract.exe",
        "tessdata_path": "engine/tessdata",
        "output_dir": "output",
        "overwrite": False,
        "log_level": "INFO"
    }

    def __init__(self):
        self.path = get_resource_path("config/config.json")
        self.config = {}
        self.load()

    def ensure_dir(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        try:
            if not self.path.exists():
                self.config = self.DEFAULT_CONFIG.copy()
                self.save()
                return

            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.config = self.DEFAULT_CONFIG.copy()
            self.config.update(data)

        except Exception:
            self.config = self.DEFAULT_CONFIG.copy()
            self.save()

    def save(self):
        self.ensure_dir()
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def update(self, values):
        if not isinstance(values, dict):
            return False
        self.config.update(values)
        self.save()
        return True
