"""Explicit application boundary for one Plugin Store window session."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from src.app.plugins.store.contracts import (
    AliveWindowProtocol,
    ApplyUninstallResult,
    UpdatePluginState,
)
from src.app.plugins.store.repository import PluginStoreRepositorySession
from src.app.plugins.store.runtime import PluginStoreRuntimeContext
from src.app.plugins.store.session import PluginStoreOperationState
from src.app.runtime.contexts.contracts import ModuleManagerProtocol
from src.app.ui_feedback import UiDispatcher
from src.app.ui_tasks import UiTaskRunner


def _is_window_alive(window: AliveWindowProtocol) -> bool:
    try:
        return bool(window.winfo_exists())
    except Exception:
        return False


@dataclass(frozen=True, slots=True)
class PluginStoreHostPort:
    runtime: PluginStoreRuntimeContext
    state: PluginStoreOperationState
    module_manager: ModuleManagerProtocol
    repository: PluginStoreRepositorySession
    dispatcher: UiDispatcher
    task_runner: UiTaskRunner
    is_alive: Callable[[], bool]
    is_plugin_installed: Callable[[str], bool]
    update_plugin_state: UpdatePluginState
    apply_uninstall_result: ApplyUninstallResult


def build_plugin_store_host_port(
    window: AliveWindowProtocol,
    *,
    runtime: PluginStoreRuntimeContext,
    state: PluginStoreOperationState,
    repository: PluginStoreRepositorySession,
    update_plugin_state: UpdatePluginState,
    apply_uninstall_result: ApplyUninstallResult,
) -> PluginStoreHostPort:
    if runtime.dispatcher is None or runtime.task_runner is None:
        raise ValueError('Plugin Store runtime requires dispatcher and task_runner.')

    return PluginStoreHostPort(
        runtime=runtime,
        state=state,
        module_manager=runtime.module_manager,
        repository=repository,
        dispatcher=runtime.dispatcher,
        task_runner=runtime.task_runner,
        is_alive=lambda: _is_window_alive(window),
        is_plugin_installed=runtime.module_manager.is_installed,
        update_plugin_state=update_plugin_state,
        apply_uninstall_result=apply_uninstall_result,
    )


__all__ = ['PluginStoreHostPort', 'build_plugin_store_host_port']
