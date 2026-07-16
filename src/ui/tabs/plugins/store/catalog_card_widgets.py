"""Tk widget builder for Plugin Store catalog cards."""

from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import TOP, X, ttk
from typing import TYPE_CHECKING

from src.ui.tabs.plugins.store.catalog_view_model import (
    PluginStoreActionViewModel,
    PluginStoreCardViewModel,
    PluginStoreMetadataViewModel,
)

if TYPE_CHECKING:
    from src.ui.tabs.plugins.store.window import MpkStore


@dataclass(frozen=True, slots=True)
class PluginStoreCardWidgets:
    frame: ttk.LabelFrame
    install_button: ttk.Button
    uninstall_button: ttk.Button


class PluginStoreCardWidgetBuilder:
    def __init__(self, window: 'MpkStore') -> None:
        self.window = window

    def build(self, card: PluginStoreCardViewModel) -> PluginStoreCardWidgets:
        plugin_frame = ttk.LabelFrame(self.window.label_frame, text=card.title)
        plugin_frame.columnconfigure(0, weight=0, minsize=70)
        plugin_frame.columnconfigure(1, weight=1)
        plugin_frame.columnconfigure(2, weight=0, minsize=100)

        self._build_icon(plugin_frame)
        info_frame = self._build_info_frame(plugin_frame)
        self._build_metadata_labels(info_frame, card.metadata)
        self._build_description(info_frame, card.metadata)
        install_button, uninstall_button = self._build_action_buttons(
            plugin_frame,
            card.actions,
        )
        return PluginStoreCardWidgets(
            frame=plugin_frame,
            install_button=install_button,
            uninstall_button=uninstall_button,
        )

    def _build_icon(self, plugin_frame: ttk.LabelFrame) -> None:
        icon_label = ttk.Label(plugin_frame, image=self.window.logo)
        icon_label.grid(row=0, column=0, sticky='nw', padx=(5, 10), pady=5)

    @staticmethod
    def _build_info_frame(plugin_frame: ttk.LabelFrame) -> ttk.Frame:
        info_frame = ttk.Frame(plugin_frame)
        info_frame.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        info_frame.columnconfigure(0, weight=1)
        return info_frame

    @staticmethod
    def _build_metadata_labels(
        info_frame: ttk.Frame,
        metadata: PluginStoreMetadataViewModel,
    ) -> None:
        ttk.Label(info_frame, text=metadata.author_label, anchor='w').grid(
            row=0,
            column=0,
            sticky='ew',
            pady=(0, 1),
        )
        ttk.Label(info_frame, text=metadata.version_label, anchor='w').grid(
            row=1,
            column=0,
            sticky='ew',
            pady=(0, 1),
        )
        ttk.Label(info_frame, text=metadata.size_label, anchor='w').grid(
            row=2,
            column=0,
            sticky='ew',
            pady=(0, 5),
        )

    @staticmethod
    def _build_description(
        info_frame: ttk.Frame,
        metadata: PluginStoreMetadataViewModel,
    ) -> None:
        desc_outer_frame = ttk.Frame(info_frame)
        desc_outer_frame.grid(row=3, column=0, sticky='nsew', pady=(2, 0))
        info_frame.rowconfigure(3, weight=1)
        desc_outer_frame.columnconfigure(0, weight=1)
        desc_outer_frame.rowconfigure(0, weight=1)
        desc_text_widget = tk.Text(
            desc_outer_frame,
            wrap=tk.WORD,
            height=5,
            relief=tk.SOLID,
            borderwidth=1,
            font=('TkDefaultFont',),
            takefocus=False,
        )
        desc_text_widget.insert(tk.END, metadata.description)
        desc_text_widget.config(state=tk.DISABLED)
        desc_scrollbar = ttk.Scrollbar(
            desc_outer_frame,
            orient=tk.VERTICAL,
            command=desc_text_widget.yview,
        )
        desc_text_widget.config(yscrollcommand=desc_scrollbar.set)
        desc_text_widget.grid(row=0, column=0, sticky='nsew')
        desc_scrollbar.grid(row=0, column=1, sticky='ns')

    def _build_action_buttons(
        self,
        plugin_frame: ttk.LabelFrame,
        actions: PluginStoreActionViewModel,
    ) -> tuple[ttk.Button, ttk.Button]:
        buttons_frame = ttk.Frame(plugin_frame)
        buttons_frame.grid(row=0, column=2, sticky='ne', padx=5, pady=5)
        def install() -> None:
            self.window.start_download_async(*actions.download_args)

        install_button = ttk.Button(
            buttons_frame,
            text=actions.install_text,
            command=install,
            width=actions.button_width,
        )
        install_button.pack(side=TOP, fill=X, pady=(0, 3))
        def uninstall() -> None:
            self.window.uninstall(actions.plugin_id)

        uninstall_button = ttk.Button(
            buttons_frame,
            text=actions.uninstall_text,
            command=uninstall,
            width=actions.button_width,
        )
        uninstall_button.pack(side=TOP, fill=X, pady=(3, 0))
        return install_button, uninstall_button


__all__ = ['PluginStoreCardWidgetBuilder', 'PluginStoreCardWidgets']
