from __future__ import annotations

import logging
from collections.abc import Sequence
from tkinter import ttk

from src.ui.localization import LocalizationCatalog
from src.ui.tabs.plugins.store import keys
from src.ui.tabs.plugins.store.button_state import PluginStoreButtonState
from src.ui.tabs.plugins.store.contracts import (
    PluginStateChangedEventProtocol,
    PluginUninstallResultView,
    StoreHostPortProtocol,
    StoreInstallResultProtocol,
    StoreNotifierProtocol,
    StoreViewStateProtocol,
)


class PluginStoreStateController:
    """Own mutable presentation state transitions for the Plugin Store."""

    def __init__(
        self,
        *,
        texts: LocalizationCatalog,
        host_port: StoreHostPortProtocol,
        notifier: StoreNotifierProtocol,
        logger: logging.Logger | None = None,
    ) -> None:
        self.texts = texts
        self.host_port = host_port
        self.logger = logger or logging.getLogger(__name__)
        self.notifier = notifier
        self.button_state = PluginStoreButtonState(
            texts=texts,
            state=self.host_port.state,
            is_alive=self.host_port.is_alive,
            logger=self.logger,
        )

    def consume_events(self, events: Sequence[PluginStateChangedEventProtocol]) -> None:
        if not self.host_port.is_alive():
            return
        refresh_all = False
        changed_ids: set[str] = set()
        for event in events:
            if not event.refresh_store:
                continue
            if event.plugin_id:
                changed_ids.add(event.plugin_id)
            else:
                refresh_all = True
        if refresh_all:
            self.refresh_visible_plugin_states()
            return
        for plugin_id in changed_ids:
            self.update_plugin_state(plugin_id)

    def refresh_visible_plugin_states(self) -> None:
        for plugin_id in self._view_state().visible_plugin_ids():
            self.update_plugin_state(plugin_id)

    def update_plugin_state(self, plugin_id: str) -> bool:
        self.logger.debug(
            "PluginStoreStateController.update_plugin_state(%s)",
            plugin_id,
        )
        if not self.host_port.is_alive() or self._controls_for(plugin_id) is None:
            return False
        return self.button_state.update_for_installed_state(
            plugin_id,
            is_installed=self.host_port.is_plugin_installed(plugin_id),
        )

    def mark_installing(self, plugin_id: str) -> None:
        install_button, _ = self.button_state.controls_for(plugin_id)
        self.button_state.set_installing(install_button)

    def update_install_progress(self, plugin_id: str, percentage: int) -> None:
        install_button, _ = self.button_state.controls_for(plugin_id)
        self.button_state.set_install_progress(install_button, percentage)

    def apply_install_result(
        self,
        plugin_id: str,
        display_name: str,
        result: StoreInstallResultProtocol,
    ) -> None:
        if self.host_port.is_alive() and not result.ok:
            self._show_install_error(display_name, result)

    def _show_install_error(
        self,
        plugin_display_name: str,
        result: StoreInstallResultProtocol,
    ) -> None:
        if result.error_kind == "dependency-not-found":
            dependency = result.failing_dependency_id or result.error_reason
            message = self.texts.resolve_required_ui_text(
                keys.DEPENDENCY_NOT_FOUND_MESSAGE_FORMAT
            ).format(plugin_name=plugin_display_name, dep_name=dependency)
            title = self.texts.resolve_required_ui_text(
                keys.DEPENDENCY_NOT_FOUND_DIALOG_TITLE
            )
        elif result.error_kind == "dependency-install-failed":
            dependency = result.failing_dependency_id or result.error_reason
            message = self.texts.resolve_required_ui_text(
                keys.DEPENDENCY_INSTALL_FAILED_MESSAGE_FORMAT
            ).format(plugin_name=plugin_display_name, dep_name=dependency)
            title = self.texts.resolve_required_ui_text(
                keys.DEPENDENCY_INSTALL_FAILED_DIALOG_TITLE
            )
        elif result.error_kind in {"network-error", "download-error"}:
            reason = result.error_reason or plugin_display_name
            message = (
                f"{self.texts.resolve_required_ui_text(keys.DOWNLOAD_FAILED_LABEL)}: {reason}"
            ).strip(": ")
            title = self.texts.resolve_required_ui_text(
                keys.DOWNLOAD_ERROR_DIALOG_TITLE
            )
        elif result.error_kind == "cancelled":
            return
        else:
            reason = result.error_reason or result.error_kind or plugin_display_name
            message = self.texts.resolve_required_ui_text(
                keys.PLUGIN_INSTALL_FAILED_MESSAGE_FORMAT
            ).format(plugin_name=plugin_display_name, reason_text=reason)
            title = self.texts.resolve_required_ui_text(
                keys.PLUGIN_INSTALL_FAILED_DIALOG_TITLE
            )
        self.notifier.show(text=message, color="orange", title=title)

    def apply_uninstall_result(
        self,
        plugin_id: str,
        result: PluginUninstallResultView,
    ) -> None:
        ok, message_text, _removed = result
        if not self.host_port.is_alive() or self._controls_for(plugin_id) is None:
            return
        if not ok and message_text:
            self.notifier.show(
                text=message_text,
                color="orange",
                title=self.texts.resolve_required_ui_text(
                    keys.UNINSTALL_ERROR_DIALOG_TITLE
                ),
            )
        self.button_state.update_for_installed_state(
            plugin_id,
            is_installed=self.host_port.is_plugin_installed(plugin_id),
        )

    def _view_state(self) -> StoreViewStateProtocol:
        return self.host_port.state

    def _controls_for(
        self,
        plugin_id: str,
    ) -> tuple[ttk.Button, ttk.Button] | None:
        return self._view_state().controls_for(plugin_id)


__all__ = ["PluginStoreStateController"]
