from __future__ import annotations

import os
import sys

from src.platform.git_repository import is_git_repository
from src.app.runtime.contexts.contracts import PresenceWindowProtocol
from src.core.file_types import gettype
from src.core.paths import prog_path
from src.core.process_registry import process_registry

if sys.platform == 'win32':
    from ctypes import windll


class States:
    """Mutable application state owned by one runtime session."""

    def __init__(self) -> None:
        self.update_window = False
        self.mpk_store = False
        self.active_mpk_store_instance: PresenceWindowProtocol | None = None
        self.debugger_window = False
        self.open_pids = process_registry.items
        self.run_source = (
            gettype(sys.argv[0]) == 'unknown'
            and is_git_repository(prog_path)
        )
        self.in_oobe = False
        self.development = False
        self.inited = False
        self.open_source_license = 'GNU AFFERO GENERAL PUBLIC LICENSE V3'
        if sys.platform == 'win32':
            self.root = bool(windll.shell32.IsUserAnAdmin())
        elif os.name == 'posix':
            self.root = os.getuid() == 0
        else:
            self.root = False


states = States()

__all__ = ['States', 'states']
