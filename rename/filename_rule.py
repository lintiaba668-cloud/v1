# -*- coding: utf-8 -*-

"""Filename generation rules.

Rules without file extension:
- start: project_name_project_code_开工
- completion: project_name_project_code
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
        code = self.normalize_code(project_code)

        if not name or not code:
            return ""

        if report_type == self.REPORT_START:
            return "%s_%s_开工" % (name, code)

        if report_type == self.REPORT_COMPLETION:
            return "%s_%s" % (name, code)

        return ""

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
        name = name.replace('\n', '')
        name = name.replace('\r', '')
        return name
