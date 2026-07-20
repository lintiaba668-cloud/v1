# -*- coding: utf-8 -*-

"""Shared application status definitions."""


class OCRStatus:
    """OCR processing lifecycle states."""

    INIT = "INIT"
    CHECKING = "CHECKING"
    READY = "READY"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"
