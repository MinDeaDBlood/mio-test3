from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class SettingsRuntimeContext:
    settings_obj: object
    cwd_path: str
    temp_path: str
    updater_func: Callable[..., object]
    theme_var: object
    language_var: object


__all__ = ['SettingsRuntimeContext']
