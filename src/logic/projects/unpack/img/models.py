from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class UnpackRequest:
    selected: list[str]
    format_name: str = 'img'

@dataclass(frozen=True)
class UnpackModuleSpec:
    key: str = 'img'
    description: str = 'raw image'
