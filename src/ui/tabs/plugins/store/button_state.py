"""State transitions for Plugin Store install and uninstall buttons."""

from __future__ import annotations

import logging
from collections.abc import Callable
from tkinter import ttk

from src.ui.localization import LocalizationCatalog
from src.ui.tabs.plugins.store.contracts import StoreViewStateProtocol
from src.ui.tabs.plugins.store import keys


def _exists(widget: ttk.Button | None) -> bool:
    if widget is None:
        return False
    try:
        return bool(widget.winfo_exists())
    except Exception:
        return False


def plugin_installed_text(texts: LocalizationCatalog) -> str:
    return texts.resolve(
        keys.INSTALLATION_COMPLETE_BUTTON,
        keys.INSTALL_BUTTON,
        context="required",
        use_reference_language=True,
    )


class PluginStoreButtonState:
    """Apply install and uninstall button states for one store window."""

    def __init__(
        self,
        *,
        texts: LocalizationCatalog,
        state: StoreViewStateProtocol,
        is_alive: Callable[[], bool],
        logger: logging.Logger | None = None,
    ) -> None:
        self.texts = texts
        self.state = state
        self.is_alive = is_alive
        self.logger = logger or logging.getLogger(__name__)

    def controls_for(
        self,
        plugin_id: str,
    ) -> tuple[ttk.Button | None, ttk.Button | None]:
        controls = self.state.controls_for(plugin_id)
        if controls is None:
            self.logger.warning(
                "PluginStoreButtonState.controls_for: controls not found for %s",
                plugin_id,
            )
            return None, None
        return controls

    def controls_exist(
        self,
        install_button: ttk.Button | None,
        uninstall_button: ttk.Button | None,
        *,
        plugin_id: str = "",
    ) -> bool:
        install_exists = _exists(install_button)
        uninstall_exists = _exists(uninstall_button)
        if plugin_id and not install_exists:
            self.logger.warning(
                "PluginStoreButtonState: install button for '%s' missing",
                plugin_id,
            )
        if plugin_id and not uninstall_exists:
            self.logger.warning(
                "PluginStoreButtonState: uninstall button for '%s' missing",
                plugin_id,
            )
        return install_exists and uninstall_exists

    def set_uninstalled(
        self,
        install_button: ttk.Button | None,
        uninstall_button: ttk.Button | None,
    ) -> None:
        if install_button is not None and _exists(install_button):
            install_button.config(
                text=self.texts.resolve_required_ui_text(keys.PLUGINS_STORE_BUTTON_STATE_INSTALL),
                state="normal",
                style="Accent.TButton",
            )
        if uninstall_button is not None and _exists(uninstall_button):
            uninstall_button.config(
                text=self.texts.resolve_required_ui_text(keys.PLUGINS_STORE_BUTTON_STATE_UNINSTALL),
                state="disabled",
                style="",
            )

    def set_installed(
        self,
        install_button: ttk.Button | None,
        uninstall_button: ttk.Button | None,
    ) -> None:
        if install_button is not None and _exists(install_button):
            install_button.config(
                text=plugin_installed_text(self.texts),
                state="disabled",
                style="",
            )
        if uninstall_button is not None and _exists(uninstall_button):
            uninstall_button.config(
                text=self.texts.resolve_required_ui_text(keys.PLUGINS_STORE_BUTTON_STATE_UNINSTALL),
                state="normal",
                style="Accent.TButton",
            )

    def set_installing(self, install_button: ttk.Button | None) -> None:
        if install_button is not None and _exists(install_button):
            install_button.config(
                state="disabled", text=self.texts.resolve_required_ui_text(keys.PLUGINS_STORE_BUTTON_STATE_READY)
            )

    def set_install_progress(
        self,
        install_button: ttk.Button | None,
        percentage: int,
    ) -> None:
        if install_button is not None and _exists(install_button) and self.is_alive():
            install_button.config(text=f"{percentage} %")

    def update_for_installed_state(
        self,
        plugin_id: str,
        *,
        is_installed: bool,
    ) -> bool:
        install_button, uninstall_button = self.controls_for(plugin_id)
        if not self.controls_exist(
            install_button,
            uninstall_button,
            plugin_id=plugin_id,
        ):
            return False
        if is_installed:
            self.set_installed(install_button, uninstall_button)
        else:
            self.set_uninstalled(install_button, uninstall_button)
        return True


__all__ = ["PluginStoreButtonState", "plugin_installed_text"]
