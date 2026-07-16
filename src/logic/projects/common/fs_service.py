from __future__ import annotations

import os

from .workspace_service import rmdir


def re_folder(path: str, quiet: bool = False, *, exists_func=os.path.exists, makedirs_func=os.makedirs, rmdir_func=rmdir) -> None:
    """Recreate a directory from scratch while preserving legacy behavior."""
    if exists_func(path):
        rmdir_func(path, quiet)
    makedirs_func(path, exist_ok=True)


__all__ = ['re_folder']
