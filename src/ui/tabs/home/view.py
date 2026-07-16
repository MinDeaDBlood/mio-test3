from __future__ import annotations

from tkinter import Label

from src.ui.localization import LocalizationCatalog
from src.ui.tabs.home.presenter import build_home_welcome_text
from src.ui.tabs.home import keys


def build_home_tab(window, *, image, texts: LocalizationCatalog) -> None:
    window._welcome_image = image
    Label(window.tab, image=image).pack(side="left", padx=0, expand=True)
    welcome_text = build_home_welcome_text(
        texts,
        "KeMiaoJiang",
        "HY-惠",
        texts.resolve_required_ui_text(keys.BRAND_NAME),
    )
    Label(
        window.tab,
        text=welcome_text,
        justify="left",
        foreground="#87CEFA",
        font=(None, 12),
    ).pack(
        side="top",
        padx=5,
        pady=120,
        expand=True,
    )


__all__ = ["build_home_tab"]
