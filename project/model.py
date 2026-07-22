# -*- coding: utf-8 -*-

from dataclasses import dataclass


@dataclass
class ProjectInfo:
    project_code: str
    project_name: str
    normalized_name: str = ''


@dataclass
class MatchResult:
    project_name: str
    project_code: str
    matched: bool
    score: float
    source: str
