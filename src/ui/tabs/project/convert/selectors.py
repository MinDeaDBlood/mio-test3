from __future__ import annotations

from tkinter import ttk


def create_format_selector(master, values, current=0, *, on_change=None):
    widget = ttk.Combobox(master, values=values, state='readonly')
    widget.current(current)
    if on_change:
        widget.bind('<<ComboboxSelected>>', lambda *x: on_change())
    widget.pack(side='left', padx=5)
    return widget
