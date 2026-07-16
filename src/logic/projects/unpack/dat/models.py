from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class UnpackRequest:
    selected: list[str]
    format_name: str = 'new.dat'

@dataclass(frozen=True)
class UnpackModuleSpec:
    key: str = 'new.dat'
    description: str = 'android dat image'
