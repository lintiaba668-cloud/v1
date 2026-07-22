# -*- coding: utf-8 -*-
"""
Power industry project alias dictionary.

Keep OCR correction rules outside core matching logic.
"""

PROJECT_ALIASES = {
    '土庄变': '上庄变',
    '兰山': '栏山',
    '401杆': '#01杆',
    '4变': '#4变'
}


def get_aliases():
    return PROJECT_ALIASES.copy()
