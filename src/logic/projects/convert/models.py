from __future__ import annotations
from dataclasses import dataclass

INPUT_FORMATS = ('raw', 'sparse', 'dat', 'br', 'xz')
OUTPUT_FORMATS = ('raw', 'sparse', 'dat', 'br')

@dataclass(frozen=True)
class ConvertSelection:
    from_format: str
    to_format: str
    items: list[str]

@dataclass(frozen=True)
class ConvertRequest:
    source_format: str
    target_format: str
    item_name: str

@dataclass(frozen=True)
class ConvertResult:
    item_name: str
    source_format: str
    target_format: str
    succeeded: bool
