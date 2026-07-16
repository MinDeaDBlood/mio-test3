from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.ui.localization import LocalizationCatalog
from src.ui.tabs.plugins.store.button_state import PluginStoreButtonState
from src.ui.tabs.plugins.store.catalog_card_widgets import PluginStoreCardWidgetBuilder
from src.ui.tabs.plugins.store.catalog_filter import build_catalog_visibility
from src.ui.tabs.plugins.store.catalog_surface import PluginStoreCatalogSurface
from src.ui.tabs.plugins.store.catalog_view_model import build_card_view_model
from src.ui.tabs.plugins.store.contracts import (
    PluginCatalogItemProtocol,
    StoreHostPortProtocol,
    StoreViewStateProtocol,
)

if TYPE_CHECKING:
    from src.ui.tabs.plugins.store.window import MpkStore


class StoreCatalogController:
    """Own Plugin Store card rendering and search filtering."""

    def __init__(
        self,
        window: "MpkStore",
        *,
        texts: LocalizationCatalog,
        host_port: StoreHostPortProtocol,
        button_width: int,
        catalog_surface: PluginStoreCatalogSurface | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.window = window
        self.texts = texts
        self.host_port = host_port
        self.catalog_surface = catalog_surface or PluginStoreCatalogSurface(window)
        self.logger = logger or logging.getLogger(__name__)
        self.button_width = button_width
        self.button_state = PluginStoreButtonState(
            texts=texts,
            state=self.host_port.state,
            is_alive=self.host_port.is_alive,
            logger=self.logger,
        )
        self.card_widget_builder = PluginStoreCardWidgetBuilder(window)

    def search_apps(self) -> None:
        if not self.host_port.is_alive():
            return
        view_state = self._view_state()
        visibility = build_catalog_visibility(
            view_state.app_info_ids(),
            view_state.catalog_items(),
            self.catalog_surface.search_text(),
        )
        for plugin_id, app_frame in view_state.app_info_items():
            if not app_frame.winfo_exists():
                continue
            should_be_visible = visibility.get(plugin_id, False)
            if should_be_visible and not app_frame.winfo_ismapped():
                self.catalog_surface.show_card(app_frame)
            elif not should_be_visible and app_frame.winfo_ismapped():
                self.catalog_surface.hide_card(app_frame)
        self.catalog_surface.sync_after_search()

    def add_app(self, items: tuple[PluginCatalogItemProtocol, ...]) -> None:
        if not self.host_port.is_alive():
            self.logger.warning("StoreCatalogController.add_app: window destroyed")
            return
        view_state = self._view_state()
        new_items_added = 0
        for item in items:
            card = build_card_view_model(
                item,
                texts=self.texts,
                button_width=self.button_width,
            )
            existing_frame = view_state.app_frame_for(card.plugin_id)
            if existing_frame is not None and existing_frame.winfo_exists():
                continue
            widgets = self.card_widget_builder.build(card)
            view_state.set_app_frame(card.plugin_id, widgets.frame)
            view_state.register_controls(
                card.plugin_id,
                widgets.install_button,
                widgets.uninstall_button,
            )
            self.button_state.update_for_installed_state(
                card.plugin_id,
                is_installed=self.host_port.is_plugin_installed(card.plugin_id),
            )
            self.catalog_surface.pack_card(widgets.frame)
            new_items_added += 1

        if new_items_added > 0 or not items:
            self.catalog_surface.sync_after_catalog_update()

    def clear(self) -> None:
        self.catalog_surface.clear_card_widgets()
        self._view_state().clear_catalog_widgets()
        self.catalog_surface.sync_after_catalog_update()

    def _view_state(self) -> StoreViewStateProtocol:
        return self.host_port.state


__all__ = ["StoreCatalogController"]
