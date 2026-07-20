# -*- coding: utf-8 -*-

"""Filename generation rules.

Only handles naming decisions.
Does not perform OCR or file operations.
"""


class FilenameRule:

    def build_filename(
        self,
        report_type,
        project_name,
        project_code=""
    ):
        """Generate target filename without extension."""

        name = self._clean_text(project_name)

        if not name:
            return ""

        if report_type == "completion":
            code = self._clean_text(project_code)

            if code:
                return f"{name}_{code}"

        return name

    def _clean_text(self, value):
        if not value:
            return ""

        return str(value).strip()
