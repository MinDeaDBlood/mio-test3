from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class UnpackRequest:
    selected: list[str]
    format_name: str = 'zst'

@dataclass(frozen=True)
class UnpackModuleSpec:
    key: str = 'zst'
    description: str = 'zstd compressed image'
