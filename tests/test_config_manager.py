# -*- coding: utf-8 -*-

"""ConfigManager tests.

Validate configuration creation, recovery and update behavior.
"""

import json

from core.config_manager import ConfigManager



def test_default_config_contains_required_keys(tmp_path, monkeypatch):
    manager = ConfigManager()

    required = {
        "ocr_path",
        "tessdata_path",
        "output_dir",
        "overwrite",
        "log_level",
    }

    assert required.issubset(set(manager.config.keys()))



def test_update_rejects_invalid_type():
    manager = ConfigManager()

    result = manager.update(None)

    assert result is False



def test_config_recovery_from_invalid_json(tmp_path, monkeypatch):
    manager = ConfigManager()

    manager.path.parent.mkdir(parents=True, exist_ok=True)

    with open(manager.path, "w", encoding="utf-8") as file:
        file.write("{invalid json")

    manager.load()

    assert "ocr_path" in manager.config
    assert manager.config["ocr_path"] == "engine/tesseract.exe"
