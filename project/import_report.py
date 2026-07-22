# -*- coding: utf-8 -*-

"""
Import operation report.
"""


class ImportReport:

    def __init__(self):
        self.success = 0
        self.failed = []
        self.duplicate = []

    def add_success(self):
        self.success += 1

    def add_failed(self, row, errors):
        self.failed.append({
            'row': row,
            'errors': errors
        })

    def add_duplicate(self, row):
        self.duplicate.append(row)

    def to_dict(self):
        return {
            'success': self.success,
            'failed': self.failed,
            'duplicate': self.duplicate
        }
