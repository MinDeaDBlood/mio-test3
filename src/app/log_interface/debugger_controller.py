from __future__ import annotations

import platform
import sys
from typing import Any


class DebuggerController:
    """Application diagnostics controller used by the debugger view."""

    def __init__(self, *, states, settings_obj, tool_log: str, namespace: dict[str, Any]) -> None:
        self.states = states
        self.settings = settings_obj
        self.tool_log = tool_log
        self.namespace = namespace

    def build_info_text(self) -> str:
        text = f"""Open Source License: {self.states.open_source_license}
Python: {sys.version}
Platform: {sys.platform}
Exec Command: {sys.argv}
Tool Version: {self.settings.version}
Source code running: {self.states.run_source}
python Implementation: {platform.python_implementation()}
Uname: {platform.uname()}
Log File: {self.tool_log}
"""
        if hasattr(sys, '_base_executable'):
            text += f'_base_executable: {sys._base_executable}'
        return text

    def setting_keys(self) -> tuple[str, ...]:
        return tuple(sorted(
            key for key in dir(self.settings)
            if not key.startswith('_') and isinstance(getattr(self.settings, key), str)
        ))

    def read_setting(self, key: str) -> str:
        if not hasattr(self.settings, key):
            raise KeyError(key)
        return str(getattr(self.settings, key))

    def write_setting(self, key: str, value: str) -> str:
        self.settings.set_value(key, value)
        return self.read_setting(key)

    def global_keys(self) -> tuple[str, ...]:
        return tuple(sorted(self.namespace))

    def read_global(self, key: str) -> str:
        return str(self.namespace.get(key, 0))

    def write_global(self, key: str, value: str) -> str:
        tokens = value.split()
        if len(tokens) >= 2:
            command, argument, *_ = tokens
            if command == 'import':
                self.namespace[key] = __import__(argument)
                return self.read_global(key)
            if command == 'global':
                self.namespace[key] = self.namespace[argument]
                return self.read_global(key)
        self.namespace[key] = value
        return self.read_global(key)


__all__ = ['DebuggerController']
