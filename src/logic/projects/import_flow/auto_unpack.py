from __future__ import annotations

import os


def list_auto_unpack_candidates(work_path: str) -> list[str]:
    """Return unique partition-like names for files imported into a project."""
    candidates: list[str] = []
    seen: set[str] = set()
    with os.scandir(work_path) as entries:
        for entry in entries:
            if not entry.is_file():
                continue
            name = entry.name.split('.', 1)[0]
            if not name or name in seen:
                continue
            seen.add(name)
            candidates.append(name)
    return candidates


__all__ = ['list_auto_unpack_candidates']
