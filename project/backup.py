# -*- coding: utf-8 -*-

"""
Project database backup utility.
"""

import shutil
from pathlib import Path


class ProjectBackup:

    def backup(self, db_path, target_path):
        source = Path(db_path)
        target = Path(target_path)

        target.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(source, target)

        return str(target)
