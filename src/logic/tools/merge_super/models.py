from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class MergeSuperStatus(str, Enum):
    MERGED = 'merged'
    NO_PROJECT = 'no_project'
    NO_SEGMENTS = 'no_segments'
    OUTPUT_EXISTS = 'output_exists'


@dataclass(frozen=True)
class MergeSuperRequest:
    output_name: str
    delete_source: bool = False


@dataclass(frozen=True)
class MergeSuperResult:
    status: MergeSuperStatus
    output_path: Path | None = None
    segment_count: int = 0
    deleted_segment_count: int = 0


__all__ = ['MergeSuperRequest', 'MergeSuperResult', 'MergeSuperStatus']
