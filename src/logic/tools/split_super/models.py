from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SplitSuperRequest:
    input_path: str
    output_directory: str
    part_count: int = 15
    block_size: int = 4096
    suffix_format: str = '.%03d'
    keep_existing: bool = False


@dataclass(frozen=True)
class SplitSuperResult:
    source_path: Path
    output_paths: tuple[Path, ...]
    block_size: int
    total_blocks: int


__all__ = ['SplitSuperRequest', 'SplitSuperResult']
