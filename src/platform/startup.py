"""Platform specific startup preparation."""

from __future__ import annotations

import logging
import os
import stat
from pathlib import Path

from src.core.paths import tool_bin


def prepare_tool_binaries(binary_directory: str | os.PathLike[str] | None = None) -> None:
    """Make bundled tools executable on POSIX systems before the first use."""
    if os.name != 'posix':
        return
    directory = Path(binary_directory or tool_bin)
    if not directory.is_dir():
        logging.warning('Bundled tool directory does not exist: %s', directory)
        return
    execute_bits = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    for path in directory.iterdir():
        if not path.is_file():
            continue
        try:
            mode = path.stat().st_mode
            if mode & execute_bits != execute_bits:
                path.chmod(mode | execute_bits)
        except OSError:
            logging.exception('Unable to make bundled tool executable: %s', path)


def prepare_startup_platform() -> None:
    """Apply early platform preparation where application startup begins."""
    if os.name == 'nt':
        from multiprocessing.dummy import freeze_support

        freeze_support()
    else:
        prepare_tool_binaries()


__all__ = ['prepare_startup_platform', 'prepare_tool_binaries']
