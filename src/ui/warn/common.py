from __future__ import annotations

from src.ui.common.windowing import Toplevel


def themed_toplevel(parent=None):
    popup = Toplevel(master=parent)
    if parent is not None and parent.winfo_exists():
        popup.transient(parent)
    return popup


def resolve_parent(master=None):
    if master is None:
        return None
    return master if master.winfo_exists() else None


def close_modal(window):
    if window.grab_current() is window:
        window.grab_release()
    window.destroy()


__all__ = ['close_modal', 'resolve_parent', 'themed_toplevel']
