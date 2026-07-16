"""Tk prompt used by the project zip packaging flow."""

from __future__ import annotations

from tkinter import BOTH, TOP, BooleanVar, IntVar, ttk

from src.ui.localization import LocalizationCatalog
from src.ui.tabs.project.pack import zip_prompt_keys as keys


def prompt_hybrid_pack_option(
    host_window, *, texts: LocalizationCatalog
) -> bool | None:
    confirm = texts.resolve_required_ui_text(keys.CONFIRM_BUTTON)
    cancel = texts.resolve_required_ui_text(keys.CANCEL_BUTTON)
    value = IntVar()
    pack_hybrid_rom = BooleanVar(value=False)

    ask = ttk.LabelFrame(host_window, text=texts.resolve_required_ui_text(keys.PROJECT_PACK_ZIP_PROMPT_PACK_ZIP))
    ask.place(relx=0.5, rely=0.5, anchor="center")
    frame_inner = ttk.Frame(ask)
    frame_inner.pack(expand=True, fill=BOTH, padx=20, pady=20)
    ttk.Label(
        frame_inner,
        text=texts.resolve_required_ui_text(keys.PROJECT_PACK_ZIP_PROMPT_REPACK_ZIP_PROMPT),
        font=(None, 15),
        wraplength=400,
    ).pack(side=TOP)
    ttk.Checkbutton(
        frame_inner,
        text=texts.resolve_required_ui_text(keys.PROJECT_PACK_ZIP_PROMPT_HYBRID_ZIP_TOOLS_DESCRIPTION),
        variable=pack_hybrid_rom,
        onvalue=True,
        offvalue=False,
    ).pack(side=TOP)

    frame_button = ttk.Frame(frame_inner)

    def close_ask(selected: int = 1):
        value.set(selected)
        ask.destroy()

    ttk.Button(frame_button, text=cancel, command=lambda: close_ask(0)).pack(
        side="left", padx=5, pady=5, fill=BOTH, expand=True
    )
    ttk.Button(
        frame_button, text=confirm, command=lambda: close_ask(1), style="Accent.TButton"
    ).pack(side="left", padx=5, pady=5, fill=BOTH, expand=True)
    frame_button.pack(fill=BOTH)
    ask.wait_window()
    if value.get() != 1:
        return None
    return bool(pack_hybrid_rom.get())


__all__ = ["prompt_hybrid_pack_option"]
