from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class UnpackRequest:
    selected: list[str]
    format_name: str = 'payload'

@dataclass(frozen=True)
class UnpackModuleSpec:
    key: str = 'payload'
    description: str = 'payload.bin partitions'
