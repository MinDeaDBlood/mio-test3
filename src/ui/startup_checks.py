from __future__ import annotations

from tkinter import Tk, messagebox


def present_fatal_startup_error(*, title: str, message: str) -> None:
    root = Tk()
    root.withdraw()
    try:
        messagebox.showerror(title, message, parent=root)
    finally:
        root.destroy()
    raise SystemExit(1)


__all__ = ["present_fatal_startup_error"]
