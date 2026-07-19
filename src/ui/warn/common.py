from __future__ import annotations

from src.ui.common.windowing import Toplevel, resolve_window_owner


def themed_toplevel(parent=None):
    return Toplevel(master=parent)


def resolve_parent(master=None):
    return resolve_window_owner(master)


def close_modal(window):
    if window.grab_current() is window:
        window.grab_release()
    window.destroy()


__all__ = ['close_modal', 'resolve_parent', 'themed_toplevel']
