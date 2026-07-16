from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class HybridPackRequest:
    output_dir: Path
    template_dir: Path
    right_device: str
    compression_threshold: int = 200 * 1024 * 1024


@dataclass(frozen=True)
class HybridImageOperation:
    image_name: str
    compressed: bool
    source_was_sparse: bool
    output_path: Path


@dataclass(frozen=True)
class HybridPackResult:
    output_dir: Path
    images_dir: Path
    operations: tuple[HybridImageOperation, ...] = field(default_factory=tuple)


__all__ = ['HybridImageOperation', 'HybridPackRequest', 'HybridPackResult']
