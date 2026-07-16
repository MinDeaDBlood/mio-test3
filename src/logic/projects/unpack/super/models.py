from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class UnpackRequest:
    selected: list[str]
    format_name: str = 'super'

@dataclass(frozen=True)
class UnpackModuleSpec:
    key: str = 'super'
    description: str = 'super image partitions'
