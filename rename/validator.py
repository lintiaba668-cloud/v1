# -*- coding: utf-8 -*-

"""Filename validation and normalization.

Responsible for Windows filename safety only.
"""

import re


class FilenameValidator:

    INVALID_CHARS = r'\\/:*?"<>|'
    MAX_LENGTH = 255

    def validate(self, filename):
        """Validate filename.

        Returns:
            tuple(bool, str)
        """

        if not filename:
            return False, "filename empty"

        if self.has_invalid_chars(filename):
            return False, "filename contains invalid characters"

        if len(filename) > self.MAX_LENGTH:
            return False, "filename too long"

        return True, ""

    def sanitize(self, filename):
        """Remove Windows forbidden characters."""

        if not filename:
            return ""

        result = filename

        for char in self.INVALID_CHARS:
            result = result.replace(char, "_")

        return result.strip()

    def has_invalid_chars(self, filename):
        return re.search(
            "[" + re.escape(self.INVALID_CHARS) + "]",
            filename
        ) is not None
