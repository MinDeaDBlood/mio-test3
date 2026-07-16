from __future__ import annotations

from pathlib import Path


def path_exists(path: str | Path) -> bool:
    return Path(path).exists()


def is_file(path: str | Path) -> bool:
    return Path(path).is_file()


def is_directory(path: str | Path) -> bool:
    return Path(path).is_dir()


def absolute_path(path: str | Path) -> str:
    return str(Path(path).expanduser().absolute())


def parent_directory(path: str | Path) -> str:
    return str(Path(path).parent)


def file_name(path: str | Path) -> str:
    return Path(path).name


__all__ = [
    "absolute_path",
    "file_name",
    "is_directory",
    "is_file",
    "parent_directory",
    "path_exists",
]
