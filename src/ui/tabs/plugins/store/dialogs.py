from __future__ import annotations

from collections.abc import Callable
from tkinter import LEFT, X, StringVar, ttk

from src.ui.common.windowing import Toplevel


def prompt_repository_url(
    *,
    parent: Toplevel,
    current_value: str,
    title: str,
    ok_text: str,
    cancel_text: str,
    move_center: Callable[[Toplevel], None],
    on_accept: Callable[[str], None],
) -> Toplevel:
    input_var = StringVar(value=current_value)
    dialog = Toplevel(master=parent)
    dialog.title(title)
    dialog.transient(parent)
    dialog.grab_set()

    ttk.Entry(dialog, textvariable=input_var, width=60).pack(
        pady=10,
        padx=10,
        fill=X,
    )
    button_frame = ttk.Frame(dialog)
    button_frame.pack(pady=5, padx=10, fill=X)

    def close_with_accept() -> None:
        value = input_var.get()
        dialog.destroy()
        on_accept(value)

    ttk.Button(
        button_frame,
        text=cancel_text,
        command=dialog.destroy,
    ).pack(side=LEFT, padx=(0, 5), expand=True, fill=X)
    ttk.Button(
        button_frame,
        text=ok_text,
        command=close_with_accept,
        style='Accent.TButton',
    ).pack(side=LEFT, padx=(5, 0), expand=True, fill=X)
    dialog.center_on_screen(force=True)
    return dialog


__all__ = ['prompt_repository_url']
