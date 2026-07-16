from __future__ import annotations

import pathlib
import sys
from collections.abc import Sequence

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


def launch_replacement_process(argv: Sequence[str]) -> int:
    """Launch the replacement instance without waiting for it to exit."""
    process = launch_detached(list(argv))
    return int(process.pid)


__all__ = ["build_restart_argv", "launch_replacement_process"]
