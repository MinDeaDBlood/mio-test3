from __future__ import annotations

import logging
import tkinter as tk
from typing import Protocol

from src.ui.assets import images


class PluginCatalogItemProtocol(Protocol):
    plugin_id: str
    display_name: str
    icon_path: object | None


class PluginCatalogIssueProtocol(Protocol):
    plugin_id: str
    message: str


class PluginCatalogResultProtocol(Protocol):
    items: tuple[PluginCatalogItemProtocol, ...]
    issues: tuple[PluginCatalogIssueProtocol, ...]


class PluginManagerCatalogPresenter:
    """Render an already loaded plugin catalog into the icon grid."""

    def __init__(self, window, *, logger=None):
        self.window = window
        self.logger = logger or logging

    def render(self, result: PluginCatalogResultProtocol) -> None:
        window = self.window
        if not hasattr(window, "pls") or not window.pls.winfo_exists():
            raise RuntimeError("Plugin icon grid is missing or destroyed")
        for issue in result.issues:
            self.logger.error("Plugin '%s': %s", issue.plugin_id, issue.message)
        loaded_ids = {item.plugin_id for item in result.items}
        for displayed_id in tuple(window.pls.apps):
            if displayed_id not in loaded_ids:
                window.pls.remove_icon(displayed_id)
                window.images_.pop(displayed_id, None)
        for item in result.items:
            photo = self._resolve_icon(item)
            if item.plugin_id in window.pls.apps:
                widget = window.pls.apps[item.plugin_id]
                if widget.winfo_exists():
                    widget.configure(image=photo, text=item.display_name)
                continue
            widget = tk.Label(
                window.pls.scrollable_frame,
                image=photo,
                compound="center",
                text=item.display_name,
                bg="#4682B4",
                wraplength=70,
                justify="center",
            )
            widget.bind(
                "<Double-Button-1>",
                lambda _event, plugin_id=item.plugin_id: window.run_plugin(plugin_id),
            )
            widget.bind(
                "<Button-3>",
                lambda event, plugin_id=item.plugin_id: window.popup(plugin_id, event),
            )
            window.pls.add_icon(widget, item.plugin_id)
        window.pls.on_frame_configure()

    def clear(self) -> None:
        window = self.window
        if not hasattr(window, "pls") or not window.pls.winfo_exists():
            raise RuntimeError("Plugin icon grid is missing or destroyed")
        window.pls.clean()
        window.pls.apps.clear()

    def _resolve_icon(self, item: PluginCatalogItemProtocol):
        window = self.window
        if item.icon_path is None:
            photo = self._photo_image(data=images.none_byte)
        else:
            try:
                from PIL.Image import open as open_img

                with open_img(item.icon_path) as image:
                    photo = self._photo_image(image.resize((70, 70)))
            except Exception as exc:
                self.logger.error(
                    "Invalid icon for plugin '%s': %s", item.plugin_id, exc
                )
                photo = self._photo_image(data=images.error_logo_byte)
        window.images_[item.plugin_id] = photo
        return photo

    @staticmethod
    def _photo_image(*args, **kwargs):
        from PIL.ImageTk import PhotoImage

        return PhotoImage(*args, **kwargs)


__all__ = ["PluginManagerCatalogPresenter"]
