# -*- coding: utf-8 -*-
"""
OCR correction layer for power engineering documents.

Correct common OCR recognition errors using domain dictionary.
"""


class OCRCorrection:

    def __init__(self):
        self.dictionary = {
            '土庄变': '上庄变',
            '湖峰线': '福岭线',
            '兰山': '栏山',
            '401杆': '#01杆',
            '1杆': '#01杆'
        }

    def correct(self, text):
        if not text:
            return ''

        result = text

        for wrong, right in self.dictionary.items():
            result = result.replace(wrong, right)

        return result

    def add_rule(self, wrong, right):
        self.dictionary[wrong] = right
