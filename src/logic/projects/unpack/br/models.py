from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class UnpackRequest:
    selected: list[str]
    format_name: str = 'new.dat.br'

@dataclass(frozen=True)
class UnpackModuleSpec:
    key: str = 'new.dat.br'
    description: str = 'brotli compressed dat image'
