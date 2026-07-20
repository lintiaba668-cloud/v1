# -*- coding: utf-8 -*-

"""Filename generation rules.

Only handles naming decisions.
Does not perform OCR or file operations.
"""


class FilenameRule:

    REPORT_START = "start"
    REPORT_COMPLETION = "completion"

    def build_filename(
        self,
        report_type,
        project_name,
        project_code=""
    ):
        """Generate target filename without extension."""

        name = self._normalize_name(project_name)

        if not name:
            return ""

        if report_type == self.REPORT_COMPLETION:
            code = self.normalize_code(project_code)

            if code:
                return "%s_%s" % (name, code)

        return name

    def normalize_code(self, code):
        """Keep engineering number characters.

        Allowed:
        - letters
        - numbers
        - '-' 
        - '#'
        """

        if not code:
            return ""

        result = []

        for char in str(code).strip():
            if char.isalnum() or char in ('-', '#'):
                result.append(char)

        return ''.join(result)

    def _normalize_name(self, value):
        if not value:
            return ""

        name = str(value).strip()

        # merge OCR multiline text
        name = name.replace('\n', '')
        name = name.replace('\r', '')

        return name
