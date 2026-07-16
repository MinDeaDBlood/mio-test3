from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BootstrapProjectPathRuntime:
    """Minimal project-path context used before full runtime windows exist.

    Keeping this tiny context in the app bootstrap layer prevents bootstrap from
    importing project workflow runtime factories just to construct ProjectManager.
    """

    workspace_path: str
    current_project_name: object | None = None


@dataclass(frozen=True)
class RuntimeBootstrapServices:
    """Typed core runtime services assembled during startup bootstrap."""

    settings: object
    module_error_codes: object
    module_manager: object
    project_manager: object

    def export_runtime_values(self) -> dict[str, object]:
        return {
            "settings": self.settings,
            "module_error_codes": self.module_error_codes,
            "module_manager": self.module_manager,
            "project_manager": self.project_manager,
        }


@dataclass(frozen=True)
class EarlyRuntimeDefaults:
    """Authoritative runtime defaults available before the Tk window exists."""

    prog_path: str
    tool_self: str
    temp: str
    log_dir: str
    tool_log: str
    context_rule_file: str
    states: object
    call: object
    module_exec: str

    def export_runtime_values(self) -> dict[str, Any]:
        return {
            "prog_path": self.prog_path,
            "tool_self": self.tool_self,
            "temp": self.temp,
            "log_dir": self.log_dir,
            "tool_log": self.tool_log,
            "context_rule_file": self.context_rule_file,
            "states": self.states,
            "call": self.call,
            "module_exec": self.module_exec,
        }


@dataclass(frozen=True)
class BootstrapWindowRuntime:
    main_window: Any
    animation: Any
    ui_scheduler: Any
    current_project_name: Any
    theme: Any
    language: Any

    def export_runtime_values(self) -> dict[str, Any]:
        return {
            "main_window": self.main_window,
            "animation": self.animation,
            "ui_scheduler": self.ui_scheduler,
            "current_project_name": self.current_project_name,
            "theme": self.theme,
            "language": self.language,
        }


@dataclass(frozen=True)
class BootstrapUiRuntime:
    unpack_view: Any
    project_menu: Any

    def export_runtime_values(self) -> dict[str, Any]:
        return {
            "unpack_view": self.unpack_view,
            "project_menu": self.project_menu,
        }


__all__ = [
    "BootstrapProjectPathRuntime",
    "BootstrapUiRuntime",
    "BootstrapWindowRuntime",
    "EarlyRuntimeDefaults",
    "RuntimeBootstrapServices",
]
