"""Narrow application ports used by the Plugin Store composition."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol

from src.logic.plugins.store_install import (
    StoreInstallResult,
)
from src.logic.plugins.events import PluginStateChangedEvent
from src.logic.plugins.uninstall.result import PluginUninstallResult


class AliveWindowProtocol(Protocol):
    def winfo_exists(self) -> bool: ...


class PluginStoreStateControllerPort(Protocol):
    def consume_events(self, events: Sequence[PluginStateChangedEvent]) -> None: ...
    def refresh_visible_plugin_states(self) -> None: ...
    def update_plugin_state(self, plugin_id: str) -> bool: ...
    def apply_uninstall_result(
        self,
        plugin_id: str,
        result: PluginUninstallResult,
    ) -> None: ...
    def mark_installing(self, plugin_id: str) -> None: ...
    def update_install_progress(self, plugin_id: str, percentage: int) -> None: ...
    def apply_install_result(
        self,
        plugin_id: str,
        display_name: str,
        result: StoreInstallResult,
    ) -> None: ...


UpdatePluginState = Callable[[str], bool]
ApplyUninstallResult = Callable[[str, PluginUninstallResult], None]
InstallFinishedCallback = Callable[[str, str, StoreInstallResult], None]


__all__ = [
    "AliveWindowProtocol",
    "ApplyUninstallResult",
    "InstallFinishedCallback",
    "PluginStoreStateControllerPort",
    "PluginUninstallResult",
    "UpdatePluginState",
]
