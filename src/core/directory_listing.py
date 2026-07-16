from __future__ import annotations

import fnmatch
from pathlib import Path


def list_matching_files(directory: str, pattern: str) -> tuple[str, tuple[str, ...]]:
    path = Path(directory or '.').expanduser().resolve()
    entries = tuple(
        sorted(
            entry.name
            for entry in path.iterdir()
            if entry.is_dir() or fnmatch.fnmatch(entry.name, pattern or '*')
        )
    )
    return str(path), ('..', *entries)


def list_directories(directory: str) -> tuple[str, tuple[str, ...]]:
    path = Path(directory or '/').expanduser().resolve()
    entries = tuple(sorted(entry.name for entry in path.iterdir() if entry.is_dir()))
    return str(path), ('..', *entries)


__all__ = ['list_directories', 'list_matching_files']
