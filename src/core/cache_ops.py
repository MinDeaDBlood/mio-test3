from __future__ import annotations

import os

from src.core.file_ops import recreate_directory


def calculate_directory_size(directory: str) -> int:
    """Return the total size of regular files below a directory."""

    total = 0
    for root, _, files in os.walk(directory):
        for name in files:
            path = os.path.join(root, name)
            if os.path.islink(path):
                continue
            total += os.path.getsize(path)
    return total


def clear_directory(directory: str) -> int:
    """Recreate a directory and return its resulting size."""

    recreate_directory(directory)
    return 0


__all__ = ["calculate_directory_size", "clear_directory"]
