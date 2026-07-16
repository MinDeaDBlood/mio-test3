"""Mutable presentation state for one Plugin Store window session."""

from __future__ import annotations

from dataclasses import dataclass, field
from tkinter import ttk

from src.ui.tabs.plugins.store.contracts import PluginCatalogItemProtocol


StoreControls = tuple[ttk.Button, ttk.Button]


@dataclass
class PluginStoreViewState:
    catalog: list[PluginCatalogItemProtocol] = field(default_factory=list)
    app_frames: dict[str, ttk.LabelFrame] = field(default_factory=dict)
    controls: dict[str, StoreControls] = field(default_factory=dict)

    def replace_catalog(self, items: tuple[PluginCatalogItemProtocol, ...]) -> None:
        self.catalog = list(items)

    def catalog_items(self) -> tuple[PluginCatalogItemProtocol, ...]:
        return tuple(self.catalog)

    def controls_for(self, plugin_id: str) -> StoreControls | None:
        return self.controls.get(plugin_id)

    def register_controls(
        self,
        plugin_id: str,
        install_button: ttk.Button,
        uninstall_button: ttk.Button,
    ) -> None:
        self.controls[plugin_id] = (install_button, uninstall_button)

    def remove_controls(self, plugin_id: str) -> None:
        self.controls.pop(plugin_id, None)

    def visible_plugin_ids(self) -> tuple[str, ...]:
        return tuple(self.controls)

    def app_frame_for(self, plugin_id: str) -> ttk.LabelFrame | None:
        return self.app_frames.get(plugin_id)

    def app_info_ids(self) -> tuple[str, ...]:
        return tuple(self.app_frames)

    def app_info_items(self) -> tuple[tuple[str, ttk.LabelFrame], ...]:
        return tuple(self.app_frames.items())

    def set_app_frame(self, plugin_id: str, frame: ttk.LabelFrame) -> None:
        self.app_frames[plugin_id] = frame

    def clear_catalog_widgets(self) -> None:
        self.app_frames.clear()
        self.controls.clear()


@dataclass
class PluginStoreSessionState(PluginStoreViewState):
    """Concrete state owner for one Plugin Store window session."""


__all__ = [
    "PluginStoreSessionState",
    "PluginStoreViewState",
    "StoreControls",
]
