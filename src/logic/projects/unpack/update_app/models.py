from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class UnpackRequest:
    selected: list[str]
    format_name: str = 'update.app'

@dataclass(frozen=True)
class UnpackModuleSpec:
    key: str = 'update.app'
    description: str = 'huawei update.app container'
