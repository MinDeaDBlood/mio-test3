from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UnpackCandidate:
    name: str
    detected_type: str | None = None
    size_bytes: int | None = None


@dataclass(frozen=True)
class PackFolderCandidate:
    name: str
    filesystem_type: str


@dataclass(frozen=True)
class ImageMetadata:
    path: str
    file_type: str
    size_bytes: int
    extra_rows: tuple[tuple[object, ...], ...] = ()


__all__ = ['ImageMetadata', 'PackFolderCandidate', 'UnpackCandidate']
