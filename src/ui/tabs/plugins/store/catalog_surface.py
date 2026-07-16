"""Narrow Tk surface used by Plugin Store catalog rendering."""

from __future__ import annotations

from dataclasses import dataclass
from tkinter import X, ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.ui.tabs.plugins.store.window import MpkStore


@dataclass(frozen=True, slots=True)
class PluginStoreCatalogSurface:
    window: 'MpkStore'

    def search_text(self) -> str:
        return self.window.search.get()

    def pack_card(self, frame: ttk.LabelFrame) -> None:
        frame.pack(padx=5, pady=5, fill=X, expand=False)

    def show_card(self, frame: ttk.LabelFrame) -> None:
        frame.pack(padx=5, pady=5, fill=X, expand=True)

    def hide_card(self, frame: ttk.LabelFrame) -> None:
        frame.pack_forget()

    def clear_card_widgets(self) -> None:
        if self.window.label_frame.winfo_exists():
            for widget in self.window.label_frame.winfo_children():
                widget.destroy()

    def sync_after_search(self) -> None:
        if self.window.label_frame.winfo_exists():
            self.window.label_frame.update_idletasks()
        if self.window.canvas.winfo_exists():
            self.window.canvas.yview_moveto(0.0)
            self.window._on_label_frame_configure()

    def sync_after_catalog_update(self) -> None:
        if self.window.label_frame.winfo_exists():
            self.window.label_frame.update_idletasks()
        if self.window.canvas.winfo_exists():
            self.window._on_label_frame_configure()


__all__ = ['PluginStoreCatalogSurface']
