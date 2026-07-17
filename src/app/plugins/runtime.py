"""Runtime boundary helpers for plugin management UI windows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from src.app.runtime.contexts.contracts import (
    HostWindowProtocol,
    ModuleErrorCodesProtocol,
    PluginGatewayProtocol,
)
from src.app.runtime.contexts.plugins import (
    resolve_module_error_codes,
    resolve_plugin_gateway,
)
from src.app.runtime.contexts.ui import resolve_ui_host_window
from src.app.ui_feedback import UiDispatcher, build_ui_dispatcher
from src.app.ui_tasks import UiTaskRunner, build_ui_task_runner


def _host_is_alive(host_window: HostWindowProtocol | None) -> bool:
    if host_window is None:
        return True
    try:
        return bool(host_window.winfo_exists())
    except Exception:
        return False


@dataclass(frozen=True, slots=True)
class PluginUiRuntimeContext:
    host_window: HostWindowProtocol
    plugin_gateway: PluginGatewayProtocol
    module_error_codes: ModuleErrorCodesProtocol
    dispatcher: UiDispatcher
    task_runner: UiTaskRunner


def build_plugin_ui_runtime_context(
    host_window: HostWindowProtocol | None = None,
) -> PluginUiRuntimeContext:
    resolved_host_window = cast(
        HostWindowProtocol,
        resolve_ui_host_window(host_window),
    )
    plugin_gateway = resolve_plugin_gateway()
    module_error_codes = cast(ModuleErrorCodesProtocol, resolve_module_error_codes())
    dispatcher = build_ui_dispatcher(host_window=resolved_host_window)
    return PluginUiRuntimeContext(
        host_window=resolved_host_window,
        plugin_gateway=plugin_gateway,
        module_error_codes=module_error_codes,
        dispatcher=dispatcher,
        task_runner=build_ui_task_runner(
            dispatcher=dispatcher,
            is_alive=lambda: _host_is_alive(resolved_host_window),
        ),
    )


__all__ = [
    "PluginUiRuntimeContext",
    "build_plugin_ui_runtime_context",
]
