from __future__ import annotations

import os
import pathlib
import sys
from collections.abc import Mapping, Sequence

from src.platform.process_launcher import launch_detached


def build_restart_argv(
    *,
    tool_self: str,
    original_argv: Sequence[str],
    executable: str | None = None,
) -> list[str]:
    executable_path = executable or sys.executable
    argv = [executable_path]
    if not pathlib.Path(tool_self).samefile(pathlib.Path(executable_path)):
        argv.append(tool_self)
    argv.extend(original_argv[1:])
    return argv


def build_restart_environment(
    base_environment: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Create an independent PyInstaller environment for an application restart."""
    environment = dict(os.environ if base_environment is None else base_environment)
    environment["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    return environment


def launch_replacement_process(
    argv: Sequence[str],
    *,
    environment: Mapping[str, str] | None = None,
) -> int:
    """Launch an independent replacement instance without waiting for it to exit."""
    process = launch_detached(
        list(argv),
        env=build_restart_environment(environment),
    )
    return int(process.pid)


__all__ = [
    "build_restart_argv",
    "build_restart_environment",
    "launch_replacement_process",
]
