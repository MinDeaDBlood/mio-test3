from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class UnpackRequest:
    selected: list[str]
    format_name: str = 'sparse'
    delegate_format: str = 'img'

@dataclass(frozen=True)
class UnpackModuleSpec:
    key: str = 'sparse'
    description: str = 'android sparse image'
    delegate_format: str = 'img'
