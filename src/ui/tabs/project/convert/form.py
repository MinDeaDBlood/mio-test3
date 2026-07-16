from __future__ import annotations

from tkinter import X, Frame, Label

from .selectors import create_format_selector


def build_conversion_header(master, state, *, on_source_change):
    frame = Frame(master)
    frame.pack(pady=5, padx=5, fill=X)
    source_selector = create_format_selector(frame, state.input_formats, 0, on_change=on_source_change)
    Label(frame, text='>>>>>>').pack(side='left', padx=5)
    target_selector = create_format_selector(frame, state.output_formats, 0)
    return frame, source_selector, target_selector
