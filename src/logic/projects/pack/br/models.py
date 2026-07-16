from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class PackOutputRequest:
    work_output: str
    partition_name: str
    output_format: str = 'br'
    brotli_level: int = 0
    dat_version: int = 4

@dataclass(frozen=True)
class PackOutputSpec:
    key: str = 'br'
    description: str = 'pack brotli-compressed dat output'
