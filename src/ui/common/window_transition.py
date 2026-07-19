"""Composited covers for visibly atomic rebuilds of mapped Tk content."""

from __future__ import annotations

import os
import tkinter as tk
from contextlib import contextmanager
from tkinter import TclError
from typing import Any, Iterator

from src.ui.common.window_paint import paint_window_now


_COVER_ATTRIBUTE = '_mio_transition_cover'


def _flush_desktop_compositor() -> None:
    if os.name != 'nt':
        return
    try:
        import ctypes

        ctypes.windll.dwmapi.DwmFlush()
    except (AttributeError, OSError):
        return


def _destroy_cover(window: Any, cover: tk.Label) -> None:
    if getattr(window, _COVER_ATTRIBUTE, None) is cover:
        setattr(window, _COVER_ATTRIBUTE, None)
    try:
        if cover.winfo_exists():
            cover.destroy()
    except TclError:
        return


def _create_cover(window: Any) -> tk.Label | None:
    if os.name != 'nt':
        return None
    existing = getattr(window, _COVER_ATTRIBUTE, None)
    if existing is not None:
        _destroy_cover(window, existing)

    cover: tk.Label | None = None
    try:
        if not window.winfo_viewable():
            return None
        window.update_idletasks()
        x = int(window.winfo_rootx())
        y = int(window.winfo_rooty())
        width = max(1, int(window.winfo_width()))
        height = max(1, int(window.winfo_height()))

        from PIL import ImageGrab, ImageTk

        snapshot = ImageGrab.grab(
            bbox=(x, y, x + width, y + height),
            all_screens=True,
        ).convert('RGB')
        photo = ImageTk.PhotoImage(snapshot, master=window)
        cover = tk.Label(
            window,
            image=photo,
            borderwidth=0,
            highlightthickness=0,
        )
        cover._mio_snapshot_photo = photo  # type: ignore[attr-defined]
        cover.place(x=0, y=0, width=width, height=height)
        cover.lift()
        paint_window_now(window, max_tk_events=8, max_native_messages=128)
        _flush_desktop_compositor()
        setattr(window, _COVER_ATTRIBUTE, cover)
        return cover
    except (AttributeError, OSError, TclError, RuntimeError, ValueError):
        if cover is not None:
            _destroy_cover(window, cover)
        return None


def _finish_covered_paint(window: Any, cover: tk.Label) -> None:
    try:
        window.update_idletasks()
        paint_window_now(window, max_tk_events=24, max_native_messages=256)
    except TclError:
        _destroy_cover(window, cover)
        return

    _destroy_cover(window, cover)
    paint_window_now(window, max_tk_events=8, max_native_messages=128)
    _flush_desktop_compositor()


@contextmanager
def snapshot_window_transition(window: Any) -> Iterator[None]:
    """Keep the last complete client image visible during a synchronous rebuild."""
    cover = _create_cover(window)
    try:
        yield
    finally:
        if cover is not None:
            _finish_covered_paint(window, cover)


__all__ = ['snapshot_window_transition']
