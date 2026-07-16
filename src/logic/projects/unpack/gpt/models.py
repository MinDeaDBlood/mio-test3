from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID


@dataclass(frozen=True)
class ExtractedGptPartition:
    name: str
    partition_id: UUID
    first_sector: int
    sector_count: int
    output_path: Path


@dataclass(frozen=True)
class GptExtractionResult:
    source_path: Path
    partitions: tuple[ExtractedGptPartition, ...]


__all__ = ['ExtractedGptPartition', 'GptExtractionResult']
