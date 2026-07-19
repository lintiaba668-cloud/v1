# -*- coding: utf-8 -*-

"""
PowerRename error code definitions.

Centralized error classification for startup, OCR and file processing.
"""


class ErrorCode:

    SUCCESS = "0000"

    ENGINE_MISSING = "E001"
    LANGUAGE_DATA_MISSING = "E002"
    CONFIG_ERROR = "E003"

    OCR_TIMEOUT = "E101"
    OCR_EXEC_FAILED = "E102"
    OCR_PARSE_FAILED = "E103"

    IMAGE_INVALID = "E201"
    IMAGE_PREPROCESS_FAILED = "E202"

    OUTPUT_FAILED = "E301"
    FILE_EXISTS = "E302"


ERROR_MESSAGE = {
    ErrorCode.SUCCESS: "success",
    ErrorCode.ENGINE_MISSING: "OCR engine missing",
    ErrorCode.LANGUAGE_DATA_MISSING: "OCR language data missing",
    ErrorCode.CONFIG_ERROR: "configuration error",
    ErrorCode.OCR_TIMEOUT: "OCR execution timeout",
    ErrorCode.OCR_EXEC_FAILED: "OCR execution failed",
    ErrorCode.OCR_PARSE_FAILED: "OCR parse failed",
    ErrorCode.IMAGE_INVALID: "invalid image",
    ErrorCode.IMAGE_PREPROCESS_FAILED: "image preprocess failed",
    ErrorCode.OUTPUT_FAILED: "output failed",
    ErrorCode.FILE_EXISTS: "file already exists"
}


def get_error_message(code):
    return ERROR_MESSAGE.get(code, "unknown error")
