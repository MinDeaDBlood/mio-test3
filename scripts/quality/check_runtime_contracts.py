#!/usr/bin/env python3
# ruff: noqa: E402
from __future__ import annotations

# Direct file execution bootstrap
import sys as _direct_sys
from pathlib import Path as _DirectPath

_DIRECT_PROJECT_ROOT = _DirectPath(__file__).resolve().parent
while _DIRECT_PROJECT_ROOT != _DIRECT_PROJECT_ROOT.parent:
    if (
        (_DIRECT_PROJECT_ROOT / "src").is_dir()
        and (_DIRECT_PROJECT_ROOT / "tests").is_dir()
        and (_DIRECT_PROJECT_ROOT / "scripts").is_dir()
    ):
        break
    _DIRECT_PROJECT_ROOT = _DIRECT_PROJECT_ROOT.parent
else:
    raise RuntimeError(f"Project root was not found for {__file__}")

_direct_root_text = str(_DIRECT_PROJECT_ROOT)
if _direct_root_text not in _direct_sys.path:
    _direct_sys.path.insert(0, _direct_root_text)
if __package__ in {None, ""}:
    _direct_relative = _DirectPath(__file__).resolve().relative_to(
        _DIRECT_PROJECT_ROOT
    ).with_suffix("")
    __package__ = ".".join(_direct_relative.parts[:-1])


import argparse
from pathlib import Path
import tkinter as tk


import inspect
from typing import Any

from src.app.runtime.contexts.contracts import (
    PluginGatewayProtocol,
    ProjectManagerProtocol,
    SettingsProtocol,
    StateBagProtocol,
    UiSchedulerProtocol,
)
from src.app.ui_scheduler import AppUiScheduler
from src.platform.runtime_paths import PLUGIN_INSTALL_DIR, SETTINGS_FILE
from src.platform.settings_repository import SettingsRepository
from src.platform.plugin_gateway import PluginGateway
from src.logic.plugins.module_manager import ModuleManager
from src.logic.projects.common.project_manager import ProjectManager
from src.logic.projects.common.runtime_context import build_project_path_runtime_context
from src.app.plugins.store.presence import PluginStorePresenceRegistry
from src.app.runtime.flags import states

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _assert_runtime_checkable(protocol, instance: Any, label: str) -> None:
    if not isinstance(instance, protocol):
        raise AssertionError(f"{label} does not satisfy {protocol.__name__}")


def _normalize_signature(sig: inspect.Signature) -> list[inspect.Parameter]:
    params = list(sig.parameters.values())
    if params and params[0].name in {"self", "cls"}:
        params = params[1:]
    return params


def _assert_method_names(
    protocol, impl_cls, method_names: tuple[str, ...], label: str
) -> None:
    for name in method_names:
        if not hasattr(impl_cls, name):
            raise AssertionError(f"{label} is missing required method {name}")
        protocol_sig = inspect.signature(getattr(protocol, name))
        impl_sig = inspect.signature(getattr(impl_cls, name))
        required_params = _normalize_signature(protocol_sig)
        implemented_params = _normalize_signature(impl_sig)
        if len(implemented_params) < len(required_params):
            raise AssertionError(
                f"{label}.{name}{impl_sig} is narrower than protocol "
                f"{protocol.__name__}.{name}{protocol_sig}"
            )
        implemented_names = {param.name for param in implemented_params}
        has_var_keyword = any(
            param.kind is inspect.Parameter.VAR_KEYWORD for param in implemented_params
        )
        for param in required_params:
            if param.kind in {
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            }:
                continue
            if not has_var_keyword and param.name not in implemented_names:
                raise AssertionError(
                    f"{label}.{name}{impl_sig} is missing protocol parameter "
                    f"{param.name!r} from "
                    f"{protocol.__name__}.{name}{protocol_sig}"
                )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Validate runtime protocol and implementation contracts.')
    arguments = (
        _direct_sys.argv[1:]
        if argv is None and __name__ == "__main__"
        else (argv or [])
    )
    parser.parse_args(arguments)
    module_manager = ModuleManager(module_dir=PLUGIN_INSTALL_DIR)
    plugin_gateway = PluginGateway(module_manager)
    settings = SettingsRepository(
        set_ini=str(SETTINGS_FILE), load=False
    )

    interpreter = tk.Tcl()
    current_project_name = tk.StringVar(master=interpreter, value="")
    project_manager = ProjectManager(
        runtime=build_project_path_runtime_context(
            workspace_path=str(PROJECT_ROOT),
            current_project_name=current_project_name,
        )
    )
    scheduler = AppUiScheduler(host_window=None)
    presence = PluginStorePresenceRegistry(states)

    _assert_runtime_checkable(PluginGatewayProtocol, plugin_gateway, "PluginGateway")
    _assert_runtime_checkable(ProjectManagerProtocol, project_manager, "ProjectManager")
    _assert_runtime_checkable(SettingsProtocol, settings, "SettingsRepository")
    _assert_runtime_checkable(UiSchedulerProtocol, scheduler, "AppUiScheduler")
    if not isinstance(presence, PluginStorePresenceRegistry):
        raise AssertionError("PluginStorePresenceRegistry construction failed")
    _assert_runtime_checkable(StateBagProtocol, states, "States")

    _assert_method_names(
        PluginGatewayProtocol,
        PluginGateway,
        (
            "request_plugin_list_refresh",
            "install",
            "uninstall",
            "check_package",
            "claim_background_load",
            "load_plugins_and_notify",
            "is_installed",
            "export",
            "create_scaffold",
            "inspect_execution",
            "execute_planned",
        ),
        "PluginGateway",
    )
    _assert_method_names(
        ProjectManagerProtocol,
        ProjectManager,
        ("current_work_path", "exist"),
        "ProjectManager",
    )
    _assert_method_names(SettingsProtocol, SettingsRepository, ("load", "set_value"), "SettingsRepository")
    _assert_method_names(
        UiSchedulerProtocol, AppUiScheduler, ("post", "start", "stop"), "AppUiScheduler"
    )
    for method_name in ("focus_existing", "mark_open", "mark_closed"):
        if not callable(getattr(PluginStorePresenceRegistry, method_name, None)):
            raise AssertionError(
                f"PluginStorePresenceRegistry is missing required method {method_name}"
            )

    print("RUNTIME_CONTRACTS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
