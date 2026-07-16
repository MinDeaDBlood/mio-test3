from __future__ import annotations

import pathlib
import subprocess
import sys
from collections.abc import Sequence


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


def run_replacement_process(argv: Sequence[str]) -> int:
    process = subprocess.Popen(list(argv))
    process.wait()
    return int(process.returncode)


__all__ = ["build_restart_argv", "run_replacement_process"]
