"""
GUI设置管理
"""

from pathlib import Path


class Settings:
    def __init__(self):
        self.output_dir = Path('output')
        self.create_excel = True
        self.create_zip = True

    def set_output(self, folder):
        self.output_dir = Path(folder)
