from __future__ import annotations

from typing import Optional
import tkinter as tk
from tkinter import BOTH, TOP, X, IntVar, Toplevel as TkToplevel
from tkinter import ttk

from src.ui.localization import LocalizationCatalog
from src.ui.common.geometry import move_center
from .models import DialogRequest
from . import dialog_keys as keys
from .common import themed_toplevel, resolve_parent, close_modal


def warn_win(
    *,
    texts: LocalizationCatalog,
    text: str = "",
    color: str = "red",
    title: str | None = None,
    ok: str | None = None,
    master: Optional[tk.Toplevel] = None,
) -> None:
    resolved_title = title or texts.resolve_required_ui_text(
        keys.WARNING_DIALOG_DEFAULT_TITLE
    )
    request = DialogRequest(
        text=text,
        title=resolved_title,
        color=color,
        ok_text=ok
        or texts.resolve_required_ui_text(keys.WARNING_DIALOG_DEFAULT_OK_BUTTON),
    )
    parent = resolve_parent(master)
    popup_window = themed_toplevel(parent)
    popup_window.title(request.title)
    if parent is not None:
        popup_window.grab_set()
    ask_frame = ttk.Frame(popup_window, padding=(20, 10))
    ask_frame.pack(expand=True, fill=BOTH)
    ttk.Label(
        ask_frame,
        text=request.text,
        font=(None, 14),
        foreground=request.color,
        wraplength=350,
        justify="center",
    ).pack(pady=(10, 20), expand=True, fill="x")
    ttk.Button(
        ask_frame,
        text=request.ok_text,
        command=lambda: close_modal(popup_window),
        style="Accent.TButton",
    ).pack(pady=(0, 10), padx=20, fill=X, ipady=4)
    popup_window.update_idletasks()
    move_center(popup_window)
    if parent is not None:
        parent.wait_window(popup_window)


def ask_win(
    text="",
    *,
    texts: LocalizationCatalog,
    ok=None,
    cancel=None,
    wait=True,
    is_top: bool = False,
    master: Optional[tk.Misc | TkToplevel] = None,
) -> int:
    request = DialogRequest(
        text=text,
        ok_text=ok
        or texts.resolve_required_ui_text(keys.CONFIRM_DIALOG_DEFAULT_OK_BUTTON),
        cancel_text=cancel
        or texts.resolve_required_ui_text(keys.CONFIRM_DIALOG_DEFAULT_CANCEL_BUTTON),
    )
    value = IntVar()
    parent = resolve_parent(master)
    if is_top or parent is None:
        ask = themed_toplevel(parent)
        move_center(ask)
    else:
        ask = ttk.LabelFrame(parent)
        ask.place(relx=0.5, rely=0.5, anchor="center")
    frame_inner = ttk.Frame(ask)
    frame_inner.pack(expand=True, fill=BOTH, padx=20, pady=20)
    ttk.Label(frame_inner, text=request.text, font=(None, 20), wraplength=400).pack(
        side=TOP
    )
    frame_button = ttk.Frame(frame_inner)

    def close_ask(value_=1):
        value.set(value_)
        ask.destroy()

    ttk.Button(
        frame_button, text=request.cancel_text, command=lambda: close_ask(0)
    ).pack(side="left", padx=5, pady=5, fill=BOTH, expand=True)
    ttk.Button(
        frame_button,
        text=request.ok_text,
        command=lambda: close_ask(1),
        style="Accent.TButton",
    ).pack(side="left", padx=5, pady=5, fill=BOTH, expand=True)
    frame_button.pack(side=TOP, fill=BOTH)
    if wait:
        ask.wait_window()
    return value.get()


def info_win(
    text: str,
    *,
    texts: LocalizationCatalog,
    title: str | None = None,
    ok: Optional[str] = None,
    master: Optional[tk.Wm] = None,
) -> None:
    request = DialogRequest(
        text=text,
        ok_text=ok
        or texts.resolve_required_ui_text(keys.INFORMATION_DIALOG_DEFAULT_OK_BUTTON),
    )
    parent = resolve_parent(master)
    dialog = themed_toplevel(parent)
    dialog.title(title or "")
    if parent is not None:
        dialog.grab_set()
    frame_inner = ttk.Frame(dialog)
    frame_inner.pack(expand=True, fill=BOTH, padx=20, pady=20)
    ttk.Label(frame_inner, text=request.text, font=(None, 20), wraplength=400).pack(
        side=TOP
    )
    ttk.Button(
        frame_inner,
        text=request.ok_text,
        command=lambda: close_modal(dialog),
        style="Accent.TButton",
    ).pack(padx=5, pady=5, fill=X, side="left", expand=True)
    dialog.update_idletasks()
    move_center(dialog)
    if parent is not None:
        parent.wait_window(dialog)
