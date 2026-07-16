from __future__ import annotations

import subprocess
from collections.abc import Mapping, Sequence


def launch_detached(
    command: str | Sequence[str],
    *,
    env: Mapping[str, str] | None = None,
) -> subprocess.Popen:
    """Launch one external process without attaching it to application output streams."""
    argv = [command] if isinstance(command, str) else list(command)
    if not argv:
        raise ValueError("Launch command is empty")
    process_environment = dict(env) if env is not None else None
    return subprocess.Popen(
        argv,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=process_environment,
    )


__all__ = ["launch_detached"]
