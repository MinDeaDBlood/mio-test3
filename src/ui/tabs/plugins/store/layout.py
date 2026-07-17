"""Tk layout composition for the Plugin Store window."""

from __future__ import annotations

import tkinter as tk
from tkinter import HORIZONTAL, LEFT, RIGHT, X, ttk
from typing import TYPE_CHECKING

from src.ui.assets import images
from src.ui.localization import LocalizationCatalog
from src.ui.tabs.plugins.store import keys

if TYPE_CHECKING:
    from PIL.ImageTk import PhotoImage
    from src.ui.tabs.plugins.store.window import MpkStore


def _photo_image(*, data: bytes) -> "PhotoImage":
    from PIL.ImageTk import PhotoImage

    return PhotoImage(data=data)


class PluginStoreLayout:
    def __init__(
        self,
        window: "MpkStore",
        *,
        texts: LocalizationCatalog,
    ) -> None:
        self.window = window
        self.texts = texts

    def build(self) -> None:
        window = self.window
        header_frame = ttk.Frame(window)
        ttk.Label(
            header_frame,
            text=self.texts.resolve_required_ui_text(keys.LAYOUT_HEADING),
            font=("TkDefaultFont", 20),
        ).pack(padx=10, pady=10, side=LEFT)
        ttk.Button(
            header_frame,
            text=self.texts.resolve_required_ui_text(keys.PLUGINS_STORE_LAYOUT_PLUGIN_REPOSITORY_URL),
            command=window.modify_repo,
        ).pack(padx=10, pady=10, side=RIGHT)
        ttk.Button(
            header_frame,
            text=self.texts.resolve_required_ui_text(keys.REFRESH_BUTTON),
            command=window.request_db_refresh,
        ).pack(padx=10, pady=10, side=RIGHT)
        header_frame.pack(padx=10, pady=10, fill=X)

        ttk.Separator(window, orient=HORIZONTAL).pack(
            padx=10,
            pady=5,
            fill=X,
        )
        window.search = ttk.Entry(window)
        window.search.pack(fill=X, padx=10, pady=5)
        window.search.bind("<Return>", lambda _event: window.search_apps())
        ttk.Separator(window, orient=HORIZONTAL).pack(
            padx=10,
            pady=5,
            fill=X,
        )

        window.logo = _photo_image(data=images.placeholder_image)
        scrollable_area_frame = tk.Frame(window)
        scrollable_area_frame.pack(
            fill="both",
            padx=10,
            pady=(0, 10),
            expand=True,
        )
        window.scrollbar = ttk.Scrollbar(
            scrollable_area_frame,
            orient="vertical",
        )
        window.canvas = tk.Canvas(
            scrollable_area_frame,
            yscrollcommand=window.scrollbar.set,
            highlightthickness=0,
            bd=0,
        )
        window.canvas.pack(side="left", fill="both", expand=True)
        window.scrollbar.config(command=window.canvas.yview)
        window.label_frame = ttk.Frame(window.canvas)
        window.label_frame_id = window.canvas.create_window(
            (0, 0),
            window=window.label_frame,
            anchor="nw",
        )
        window.label_frame.bind("<Configure>", window._on_label_frame_configure)
        window.canvas.bind("<Configure>", window._on_canvas_configure)
        window.canvas.bind("<MouseWheel>", window._on_mousewheel_canvas)
        window.canvas.bind("<Button-4>", window._on_mousewheel_canvas)
        window.canvas.bind("<Button-5>", window._on_mousewheel_canvas)

    def on_mousewheel_canvas(self, event: tk.Event) -> None:
        window = self.window
        if not window.canvas.winfo_exists():
            return
        if event.num == 4:
            window.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            window.canvas.yview_scroll(1, "units")
        elif event.delta:
            window.canvas.yview_scroll(int(-event.delta / 120), "units")

    def on_label_frame_configure(self, event: object | None = None) -> None:
        window = self.window
        if not (window.canvas.winfo_exists() and window.label_frame.winfo_exists()):
            return
        window.canvas.config(scrollregion=window.canvas.bbox("all"))
        window.label_frame.update_idletasks()
        canvas_height = window.canvas.winfo_height()
        content_height = window.label_frame.winfo_reqheight()
        if content_height > canvas_height:
            if not window.scrollbar.winfo_ismapped():
                window.scrollbar.pack(side="right", fill="y")
        elif window.scrollbar.winfo_ismapped():
            window.scrollbar.pack_forget()

    def on_canvas_configure(self, event: tk.Event) -> None:
        window = self.window
        if not (window.canvas.winfo_exists() and window.label_frame.winfo_exists()):
            return
        window.canvas.itemconfig(window.label_frame_id, width=event.width)
        window.label_frame.config(width=event.width)
        window.label_frame.update_idletasks()
        self.on_label_frame_configure()


__all__ = ["PluginStoreLayout"]
