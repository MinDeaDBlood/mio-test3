from __future__ import annotations

import os
import tkinter as tk
from collections.abc import Callable, Iterable
from tkinter import TclError, Toplevel as TkToplevel, X, ttk
from typing import Any
from weakref import ReferenceType, ref

from src.ui.common import windowing_keys as keys
from src.ui.common.window_appearance import register_window
from src.ui.localization import LocalizationCatalog



_MAIN_WINDOW: ReferenceType[Any] | None = None


def register_main_window(window: Any) -> None:
    """Register the application root used to own windows opened without a master."""
    global _MAIN_WINDOW
    _MAIN_WINDOW = ref(window)


def _registered_main_window() -> Any | None:
    if _MAIN_WINDOW is None:
        return None
    return _MAIN_WINDOW()

def _window_exists(window: Any | None) -> bool:
    if window is None:
        return False
    try:
        return bool(window.winfo_exists())
    except (AttributeError, TclError):
        return False


def _window_is_visible(window: Any | None) -> bool:
    if window is None or not _window_exists(window):
        return False
    try:
        return str(window.state()) != "withdrawn"
    except (AttributeError, TclError):
        return True


def _as_toplevel(window: Any | None) -> Any | None:
    if window is None or not _window_exists(window):
        return None
    try:
        top = window.winfo_toplevel()
    except (AttributeError, TclError):
        return None
    return top if _window_exists(top) else None


def resolve_window_owner(master: Any | None = None) -> Any | None:
    """Return the visible MIO Kitchen window that should own a new dialog."""
    explicit_owner = _as_toplevel(master)
    if explicit_owner is not None:
        return explicit_owner

    root = _registered_main_window()
    if root is None or not _window_exists(root):
        return None

    try:
        focused = root.focus_get()
    except (AttributeError, TclError):
        focused = None
    focused_owner = _as_toplevel(focused)
    if _window_is_visible(focused_owner):
        return focused_owner

    return root if _window_exists(root) else None


def present_window(window: Any, *, owner: Any | None = None) -> None:
    """Place a visible application window above its owner and give it focus."""
    if not _window_exists(window) or not _window_is_visible(window):
        return

    resolved_owner = resolve_window_owner(owner)
    if resolved_owner is window or not _window_is_visible(resolved_owner):
        resolved_owner = None

    if resolved_owner is not None:
        try:
            window.transient(resolved_owner)
        except (AttributeError, TclError):
            pass

    try:
        window.lift()
    except (AttributeError, TclError):
        pass

    if os.name == "nt":
        try:
            window.attributes("-topmost", True)
            window.after(100, lambda: _release_temporary_topmost(window))
        except (AttributeError, TclError):
            pass

    try:
        window.focus_force()
    except (AttributeError, TclError):
        try:
            window.focus_set()
        except (AttributeError, TclError):
            pass


def _release_temporary_topmost(window: Any) -> None:
    if not _window_exists(window):
        return
    try:
        window.attributes("-topmost", False)
    except (AttributeError, TclError):
        pass


class Toplevel(TkToplevel):
    """Project window with shared ownership, foreground behavior and centering."""

    def __init__(
        self,
        master: tk.Misc | None = None,
        *,
        center_on_open: bool = True,
        focus_on_open: bool = True,
        **kwargs: Any,
    ) -> None:
        owner = resolve_window_owner(master)
        super().__init__(master=master, **kwargs)
        self._window_owner = owner
        self._focus_on_open = focus_on_open
        self._centered_once = False
        register_window(self)

        if owner is not None and owner is not self and _window_is_visible(owner):
            try:
                self.transient(owner)
            except TclError:
                pass

        self.bind("<Map>", self._on_window_mapped, add="+")
        if center_on_open:
            self.center_after_layout()
        if focus_on_open:
            self.after_idle(self.present_in_foreground)

    def _on_window_mapped(self, _event: object) -> None:
        if self._focus_on_open:
            self.present_in_foreground()

    def present_in_foreground(self) -> None:
        present_window(self, owner=self._window_owner)

    def center_after_layout(self, *, force: bool = False) -> None:
        self.after_idle(lambda: self.center_on_screen(force=force))

    def center_on_screen(self, *, force: bool = False) -> None:
        if self._centered_once and not force:
            return
        try:
            from src.ui.common.geometry import move_center

            move_center(self)
        except (TclError, RuntimeError):
            return
        self._centered_once = True


class CustomControls:
    def __init__(
        self,
        *,
        texts: LocalizationCatalog,
        choose_file: Callable[[], str],
        choose_directory: Callable[[], str],
    ) -> None:
        self._texts = texts
        self._choose_file = choose_file
        self._choose_directory = choose_directory

    def filechose(
        self,
        master: tk.Misc,
        textvariable: tk.Variable,
        text: str,
        *,
        is_folder: bool = False,
        browse_text: str | None = None,
    ) -> ttk.Frame:
        frame = ttk.Frame(master)
        frame.pack(fill=X)
        ttk.Label(
            frame,
            text=text,
            width=15,
            font=("TkDefaultFont", 12),
        ).pack(side="left", padx=10, pady=10)
        ttk.Entry(frame, textvariable=textvariable).pack(
            side="left",
            padx=5,
            pady=5,
        )
        chooser = self._choose_directory if is_folder else self._choose_file
        ttk.Button(
            frame,
            text=browse_text
            or self._texts.resolve_required_ui_text(keys.COMMON_WINDOWING_BROWSE),
            command=lambda: textvariable.set(chooser()),
        ).pack(side="left", padx=10, pady=10)
        return frame

    @staticmethod
    def combobox(
        master: tk.Misc,
        textvariable: tk.Variable,
        values: Iterable[str],
        text: str,
    ) -> ttk.Combobox:
        frame = ttk.Frame(master)
        frame.pack(fill=X)
        ttk.Label(
            frame,
            text=text,
            width=15,
            font=("TkDefaultFont", 12),
        ).pack(side="left", padx=10, pady=10)
        combo = ttk.Combobox(
            frame,
            textvariable=textvariable,
            values=tuple(values),
            state="readonly",
        )
        combo.pack(side="left", padx=5, pady=5)
        combo_values = tuple(combo["values"])
        if combo_values and not textvariable.get():
            textvariable.set(combo_values[0])
        return combo


__all__ = [
    "CustomControls",
    "Toplevel",
    "present_window",
    "register_main_window",
    "resolve_window_owner",
]
