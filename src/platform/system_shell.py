from __future__ import annotations

import os
import sys
import webbrowser
from pathlib import Path

from src.platform.process_launcher import launch_detached


def open_in_file_manager(path: str | Path) -> None:
    """Open an existing path in the operating system file manager."""
    target = Path(path).expanduser().resolve()
    if not target.exists():
        raise FileNotFoundError(target)
    if os.name == "nt":
        os.startfile(str(target))  # type: ignore[attr-defined]
        return
    command = (
        ["open", str(target)] if sys.platform == "darwin" else ["xdg-open", str(target)]
    )
    launch_detached(command)


def open_external_url(url: str) -> bool:
    """Open an external URL through the platform browser at the application boundary."""
    return bool(webbrowser.open(url))


__all__ = ["open_external_url", "open_in_file_manager"]
