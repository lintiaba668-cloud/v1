"""
处理结果记录
"""

from dataclasses import dataclass


@dataclass
class RenameResult:
    source: str
    target: str = ''
    project_name: str = ''
    project_code: str = ''
    status: str = ''
    message: str = ''
