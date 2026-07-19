from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import Label, ttk

from src.ui.tabs.about.click_state import AboutTabClickState
from src.ui.tabs.about.presenter import AboutTabPresenter


def build_about_tab(
    window,
    *,
    presenter: AboutTabPresenter,
    debugger_is_open: Callable[[], bool],
    open_debugger: Callable[[], object],
    open_repository: Callable[[], object],
    is_pro_mode: bool,
) -> None:
    window.rotate_angle = 0
    state = AboutTabClickState()
    about_spec = presenter.build_spec()

    def get_color():
        color, should_open_debugger = state.next_color_and_debug(debugger_is_open())
        if should_open_debugger:
            open_debugger()
        return color

    def update_angle():
        window.rotate_angle = (window.rotate_angle + 10) % 360
        canvas.itemconfigure(text_item, angle=window.rotate_angle)

    canvas = tk.Canvas(window.tab4, width=400, height=100)
    canvas.pack()
    text_item = canvas.create_text(
        200, 50, text=about_spec.brand_heading, font=("Arial", 30), fill="white"
    )
    canvas.tag_bind(text_item, "<B1-Motion>", lambda _event: update_angle())
    canvas.tag_bind(
        text_item,
        "<Button-1>",
        lambda _event: canvas.itemconfigure(text_item, fill=get_color()),
    )
    Label(
        window.tab4, text=about_spec.description_text, font=(None, 15), fg="#00BFFF"
    ).pack(padx=10, pady=10)
    Label(
        window.tab4, text=about_spec.runtime_text, font=(None, 11), fg="#00aaff"
    ).pack(padx=10, pady=10)
    ttk.Label(
        window.tab4,
        text=about_spec.language_credit,
        foreground="orange",
    ).pack()
    Label(window.tab4, text=about_spec.footer_text, font=(None, 10)).pack(
        padx=10, pady=10, side="bottom"
    )
    if about_spec.link_title:
        ttk.Label(window.tab4, text=about_spec.link_title, style="Link.TLabel").pack()
    link = ttk.Label(
        window.tab4, text=about_spec.github_text, cursor="hand2", style="Link.TLabel"
    )
    link.bind("<Button-1>", lambda _event: open_repository())
    if not is_pro_mode:
        link.pack()


__all__ = ["build_about_tab"]
