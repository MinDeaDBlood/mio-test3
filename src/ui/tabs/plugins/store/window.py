from __future__ import annotations

import tkinter as tk
from collections.abc import Sequence
from typing import TYPE_CHECKING
from tkinter import ttk

from src.ui.common.windowing import Toplevel
from src.ui.localization import LocalizationCatalog
from src.ui.tabs.plugins.store import keys
from src.ui.tabs.plugins.store.contracts import (
    ClosableBindingProtocol,
    PluginCatalogItemProtocol,
    PluginStateChangedEventProtocol,
    StoreCatalogProtocol,
    StoreCompositionProtocol,
    StoreLayoutProtocol,
    StoreWindowControllerProtocol,
)
from src.ui.tabs.plugins.store.state import PluginStoreSessionState

if TYPE_CHECKING:
    from PIL.ImageTk import PhotoImage


class MpkStore(Toplevel):
    """Plugin Store view assembled by the application composition root."""

    search: ttk.Entry
    logo: PhotoImage
    scrollbar: ttk.Scrollbar
    canvas: tk.Canvas
    label_frame: ttk.Frame
    label_frame_id: int

    def __init__(self, *, texts: LocalizationCatalog) -> None:
        super().__init__(auto_show=False)
        self.texts = texts
        self.title(texts.resolve_required_ui_text(keys.WINDOW_TITLE))
        self.minsize(500, 400)
        self.store_state = PluginStoreSessionState()
        self.controller: StoreWindowControllerProtocol | None = None
        self.layout: StoreLayoutProtocol | None = None
        self.catalog: StoreCatalogProtocol | None = None
        self._plugin_event_binding: ClosableBindingProtocol | None = None
        self.protocol("WM_DELETE_WINDOW", self._on_close_window)

    def attach(self, composition: StoreCompositionProtocol) -> None:
        self._plugin_event_binding = composition.event_binding
        self.catalog = composition.catalog
        self.layout = composition.layout
        self.controller = composition.controller

    def open(self) -> None:
        self._require_controller().open()
        self.deiconify()

    def start_download_async(
        self,
        files: tuple[str, ...],
        size: int,
        plugin_id: str,
        dependencies: tuple[str, ...],
    ) -> bool:
        return self._require_controller().start_download_async(
            files,
            size,
            plugin_id,
            dependencies,
        )

    def start_uninstall_async(self, plugin_id: str) -> bool:
        return self._require_controller().start_uninstall_async(plugin_id)

    def _on_mousewheel_canvas(self, event: tk.Event) -> None:
        self._require_layout().on_mousewheel_canvas(event)

    def _on_label_frame_configure(self, event: object | None = None) -> None:
        self._require_layout().on_label_frame_configure(event)

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self._require_layout().on_canvas_configure(event)

    def _consume_plugin_events(
        self,
        events: Sequence[PluginStateChangedEventProtocol],
    ) -> None:
        self._require_controller().consume_plugin_events(events)

    def _on_close_window(self) -> None:
        if self.controller is not None:
            self.controller.close()
        if self._plugin_event_binding is not None:
            self._plugin_event_binding.close()
        if hasattr(self, "canvas") and self.canvas.winfo_exists():
            self.canvas.unbind("<MouseWheel>")
            self.canvas.unbind("<Button-4>")
            self.canvas.unbind("<Button-5>")
        self.destroy()

    def search_apps(self) -> None:
        self._require_catalog().search_apps()

    def add_app(self, items: tuple[PluginCatalogItemProtocol, ...]) -> None:
        self._require_catalog().add_app(items)

    def uninstall(self, plugin_id: str) -> bool:
        return self.start_uninstall_async(plugin_id)

    def clear(self) -> None:
        self._require_catalog().clear()

    def modify_repo(self) -> object:
        return self._require_controller().modify_repo()

    def request_db_refresh(self, refresh: bool = False) -> bool:
        return self._require_controller().request_db_refresh(refresh)

    def get_db(self, refresh: bool = False) -> bool:
        return self.request_db_refresh(refresh)

    def _require_controller(self) -> StoreWindowControllerProtocol:
        if self.controller is None:
            raise RuntimeError(
                "Plugin Store view is not attached to its application composition."
            )
        return self.controller

    def _require_layout(self) -> StoreLayoutProtocol:
        if self.layout is None:
            raise RuntimeError("Plugin Store layout is not attached.")
        return self.layout

    def _require_catalog(self) -> StoreCatalogProtocol:
        if self.catalog is None:
            raise RuntimeError("Plugin Store catalog is not attached.")
        return self.catalog


__all__ = ["MpkStore"]
