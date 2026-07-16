from __future__ import annotations

import subprocess
from collections.abc import Sequence


def launch_detached(command: str | Sequence[str]) -> subprocess.Popen:
    """Launch one external process without attaching it to application output streams."""
    argv = [command] if isinstance(command, str) else list(command)
    if not argv:
        raise ValueError('Launch command is empty')
    return subprocess.Popen(argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


__all__ = ['launch_detached']
