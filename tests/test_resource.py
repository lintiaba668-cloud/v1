# -*- coding: utf-8 -*-

"""Resource path tests."""

from pathlib import Path

from core.resource import (
    get_base_path,
    get_resource_path,
    get_engine_path,
    get_config_path,
    get_output_path,
    get_log_path,
)



def test_base_path_is_absolute():
    assert get_base_path().is_absolute()



def test_resource_path_join():
    result = get_resource_path("engine/tesseract.exe")

    assert isinstance(result, Path)
    assert str(result).endswith("engine/tesseract.exe")



def test_standard_resource_directories():
    assert get_engine_path().name == "engine"
    assert get_config_path().name == "config"
    assert get_output_path().name == "output"
    assert get_log_path().name == "logs"
