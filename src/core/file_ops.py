from __future__ import annotations

from pathlib import Path
import shutil


def remove_path(path: str | Path, *, missing_ok: bool = True) -> bool:
    """Remove one file, symlink or directory with one deterministic strategy."""
    target = Path(path)
    if target.is_symlink() or target.is_file():
        target.unlink(missing_ok=missing_ok)
        return True
    if target.is_dir():
        shutil.rmtree(target)
        return True
    if missing_ok:
        return False
    raise FileNotFoundError(str(target))


def recreate_directory(path: str | Path) -> Path:
    """Replace a directory with one empty directory using one deterministic path."""
    target = Path(path)
    remove_path(target, missing_ok=True)
    target.mkdir(parents=True, exist_ok=False)
    return target


__all__ = ['recreate_directory', 'remove_path']
