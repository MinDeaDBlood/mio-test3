from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class PackOutputRequest:
    work_output: str
    partition_name: str
    output_format: str = 'raw'
    brotli_level: int = 0
    dat_version: int = 4

@dataclass(frozen=True)
class PackOutputSpec:
    key: str = 'raw'
    description: str = 'pack raw image output'
