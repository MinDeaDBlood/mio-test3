# Copyright (C) 2022-2025 The MIO-KITCHEN-SOURCE Project
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0.
from __future__ import annotations

import os
import platform
import sys
from pathlib import Path

# Prevent system errors when Android payload manifests contain very large ints.
if hasattr(sys, 'set_int_max_str_digits'):
    sys.set_int_max_str_digits(0)


def resolve_program_root(
    *,
    frozen: bool | None = None,
    executable: str | None = None,
    module_file: str | None = None,
    platform_name: str | None = None,
) -> Path:
    """Resolve the application root from the deployment mode, never from argv."""
    if frozen is None:
        is_frozen = bool(sys.frozen) if hasattr(sys, 'frozen') else False
    else:
        is_frozen = frozen
    active_platform = platform.system() if platform_name is None else platform_name

    if is_frozen:
        root = Path(executable or sys.executable).resolve().parent
        if active_platform == 'Darwin' and root.parts[-3:] == ('tool.app', 'Contents', 'MacOS'):
            return root.parents[2]
        return root

    source_file = Path(module_file or __file__).resolve()
    return source_file.parents[2]


prog_path = str(resolve_program_root())
tool_bin = os.path.join(prog_path, 'bin', platform.system(), platform.machine()) + os.sep
__all__ = [
    'prog_path',
    'resolve_program_root',
    'tool_bin',
]
