"""Store specific runtime boundary for the plugin repository window."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from src.app.plugins.store.presence import (
    PluginStorePresenceRegistry,
    PluginStoreStateBagProtocol,
)
from src.app.runtime.contexts.contracts import (
    HostWindowProtocol,
    ModuleErrorCodesProtocol,
    PluginGatewayProtocol,
    SettingsProtocol,
)
from src.app.runtime.contexts.plugins import (
    resolve_module_error_codes,
    resolve_plugin_gateway,
)
from src.app.runtime.contexts.settings import resolve_settings, resolve_states
from src.app.runtime.contexts.ui import resolve_ui_host_window
from src.app.ui_feedback import UiDispatcher, build_ui_dispatcher
from src.app.ui_tasks import UiTaskRunner, build_ui_task_runner
from src.platform.runtime_paths import PLUGIN_DOWNLOAD_DIR


def _host_is_alive(host_window: HostWindowProtocol) -> bool:
    try:
        return bool(host_window.winfo_exists())
    except Exception:
        return False


@dataclass(frozen=True, slots=True)
class PluginStoreRuntimeContext:
    host_window: HostWindowProtocol
    settings: SettingsProtocol
    plugin_gateway: PluginGatewayProtocol
    module_error_codes: ModuleErrorCodesProtocol
    presence: PluginStorePresenceRegistry
    temp_path: str
    dispatcher: UiDispatcher
    task_runner: UiTaskRunner


def build_plugin_store_runtime_context(
    host_window: HostWindowProtocol | None = None,
) -> PluginStoreRuntimeContext:
    resolved_host_window = cast(
        HostWindowProtocol,
        resolve_ui_host_window(host_window),
    )
    settings = cast(SettingsProtocol, resolve_settings())
    plugin_gateway = resolve_plugin_gateway()
    module_error_codes = cast(ModuleErrorCodesProtocol, resolve_module_error_codes())
    states = cast(PluginStoreStateBagProtocol, resolve_states())
    dispatcher = build_ui_dispatcher(host_window=resolved_host_window)
    presence = PluginStorePresenceRegistry(states)
    return PluginStoreRuntimeContext(
        host_window=resolved_host_window,
        settings=settings,
        plugin_gateway=plugin_gateway,
        module_error_codes=module_error_codes,
        presence=presence,
        temp_path=str(PLUGIN_DOWNLOAD_DIR),
        dispatcher=dispatcher,
        task_runner=build_ui_task_runner(
            dispatcher=dispatcher,
            is_alive=lambda: _host_is_alive(resolved_host_window),
        ),
    )


__all__ = ["PluginStoreRuntimeContext", "build_plugin_store_runtime_context"]
