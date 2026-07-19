# -*- coding: utf-8 -*-
"""
PowerRename resource path manager.

Provides unified resource locating for:
- Python source execution
- PyInstaller frozen execution
"""

import sys
from pathlib import Path


def get_base_path():
    """Return application root directory."""
    try:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parent.parent
    except Exception:
        return Path.cwd()


def get_resource_path(relative_path):
    """Return absolute path for bundled resources."""
    try:
        return get_base_path() / relative_path
    except Exception:
        return Path(relative_path)


def get_engine_path():
    return get_resource_path("engine")


def get_config_path():
    return get_resource_path("config")


def get_output_path():
    return get_resource_path("output")


def get_log_path():
    return get_resource_path("logs")
