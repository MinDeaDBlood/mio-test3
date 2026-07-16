"""updater-script to fs_config conversion for import flow."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from src.core import extra
from src.core.file_finder import findfile
from src.core.json_store import JsonEdit


def script2fs(
    path: str,
    *,
    findfile_func: Callable[[str, str], str] = findfile,
    script2fs_context_func: Callable[[str, str, str], object] = extra.script2fs_context,
    json_edit_cls: Callable[[str], Any] = JsonEdit,
) -> None:
    """Convert legacy updater-script metadata into project fs_config files."""
    if not os.path.exists(os.path.join(path, 'system', 'app')):
        return
    config_dir = os.path.join(path, 'config')
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    script2fs_context_func(findfile_func('updater-script', f'{path}/META-INF'), config_dir, path)
    json_ = json_edit_cls(os.path.join(config_dir, 'parts_info'))
    parts = json_.read()
    for value in os.listdir(path):
        if os.path.exists(os.path.join(config_dir, f'{value}_fs_config')) and value not in parts.keys():
            parts[value] = 'ext'
    json_.write(parts)


__all__ = ['script2fs']
