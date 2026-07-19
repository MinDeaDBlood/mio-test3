from __future__ import annotations

import os
import tkinter as tk
from tkinter import TclError, Toplevel as TkToplevel
from typing import Any
from weakref import ReferenceType, ref

from src.ui.common.window_controls import CustomControls
from src.ui.common.window_appearance import current_window_alpha, register_window
from src.ui.common.window_paint import (
    paint_window_now,
    set_native_window_alpha,
    set_native_window_cloaked,
    stage_window_offscreen,
)
from src.ui.common.titlebar import set_title_bar_color

_MAIN_WINDOW: ReferenceType[Any] | None = None
def _flush_desktop_compositor() -> None:
    if os.name != "nt":
        return
    try:
        import ctypes

        ctypes.windll.dwmapi.DwmFlush()
    except (AttributeError, OSError):
        return


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


def _window_manager_state(window: Any) -> str | None:
    """Read the native Tk window state without calling a shadowable widget method.

    Several MIO Kitchen windows legitimately store their presentation model in an
    instance attribute named ``state``. Calling ``window.state()`` therefore is
    unsafe because the instance attribute can hide Tk's method. Querying Tk
    directly avoids that name collision for every Toplevel subclass.
    """
    try:
        return str(window.tk.call("wm", "state", window._w))
    except (AttributeError, TclError):
        return None


def _window_is_visible(window: Any | None) -> bool:
    if window is None or not _window_exists(window):
        return False
    state = _window_manager_state(window)
    return state != "withdrawn" if state is not None else True


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


def present_window(
    window: Any,
    *,
    owner: Any | None = None,
    transient: bool = False,
) -> bool:
    """Place a visible application window above its owner and give it focus."""
    if not _window_exists(window) or not _window_is_visible(window):
        return False

    resolved_owner = resolve_window_owner(owner)
    if resolved_owner is window or not _window_is_visible(resolved_owner):
        resolved_owner = None

    if transient and resolved_owner is not None:
        try:
            window.transient(resolved_owner)
        except (AttributeError, TclError):
            pass

    try:
        window.lift()
    except (AttributeError, TclError):
        pass

    try:
        window.focus_force()
    except (AttributeError, TclError):
        try:
            window.focus_set()
        except (AttributeError, TclError):
            pass
    return True


class Toplevel(TkToplevel):
    """Project window with shared ownership, foreground behavior and centering."""

    def __init__(
        self,
        master: tk.Misc | None = None,
        *,
        center_on_open: bool = True,
        focus_on_open: bool = True,
        auto_show: bool = True,
        **kwargs: Any,
    ) -> None:
        owner = resolve_window_owner(master)
        super().__init__(master=master, **kwargs)
        # A native Toplevel starts life visible. Keep it withdrawn until the
        # subclass has built its complete widget tree; otherwise any layout or
        # DWM flush performed during construction can expose the system's light
        # client background for a frame.
        TkToplevel.withdraw(self)
        self._window_owner = owner
        self._transient_owner_enabled = master is not None
        self._transient_owner_attached = False
        self._center_on_open = center_on_open
        self._focus_on_open = focus_on_open
        self._auto_show = auto_show
        self._centered_once = False
        self._initial_show_scheduled = False
        self._initial_show_in_progress = False
        self._initial_show_complete = False
        self._initial_show_generation = 0
        self._foreground_scheduled = False
        self._foreground_presented = False
        register_window(self)

        self.bind("<Map>", self._on_window_mapped, add="+")
        if auto_show:
            self._schedule_initial_show()

    def _schedule_initial_show(self) -> None:
        if (
            self._initial_show_scheduled
            or self._initial_show_in_progress
            or self._initial_show_complete
        ):
            return
        self._initial_show_scheduled = True
        # Timer callbacks are deliberately used instead of after_idle:
        # update_idletasks() may run idle callbacks from inside a constructor.
        try:
            self.after(0, self._show_when_ready)
        except TclError:
            self._initial_show_scheduled = False

    def _show_when_ready(self) -> None:
        self._initial_show_scheduled = False
        if (
            self._initial_show_complete
            or self._initial_show_in_progress
            or not _window_exists(self)
        ):
            return
        self._initial_show_in_progress = True
        self._initial_show_generation += 1
        generation = self._initial_show_generation

        # On Windows, assigning ``wm transient`` to an already mapped Tk
        # window replaces its outer TkTopLevel HWND.  That discarded the
        # transparent, fully painted wrapper and briefly exposed a fresh white
        # one.  Establish native ownership while still withdrawn so the first
        # mapped HWND is also the final HWND.
        try:
            transient_enabled = bool(self._transient_owner_enabled)
            transient_owner = self._window_owner
        except AttributeError:
            transient_enabled = False
            transient_owner = None
        if transient_enabled and _window_exists(transient_owner):
            try:
                self.transient(transient_owner)
                self._transient_owner_attached = True
            except (AttributeError, TclError):
                self._transient_owner_attached = False

        # register_window is idempotent and now themes the children that were
        # created after the base Toplevel constructor returned.
        try:
            register_window(self)
            if self._center_on_open and not self._centered_once:
                self.center_on_screen()
        except (RuntimeError, TclError):
            self._abort_initial_show(generation)
            return
        gated = False
        target_geometry = None
        if os.name == "nt":
            try:
                # Alpha/cloak support differs between Windows builds. Mapping
                # the real, fully themed window off-screen is the reliable
                # fallback: incomplete native paints never reach the desktop.
                target_geometry = stage_window_offscreen(self)
                # A mapped Tk window needs at least one display-idle pass before
                # Windows has a complete client surface.  Keep that first native
                # frame fully transparent instead of exposing the class brush.
                self.attributes("-alpha", 0.0)
                set_native_window_alpha(self, 0.0)
                set_native_window_cloaked(self, True)
                self._appearance_alpha_gated = True
                gated = True
            except TclError:
                gated = False
            set_title_bar_color(self, True)
        try:
            TkToplevel.deiconify(self)
            if gated:
                set_native_window_alpha(self, 0.0)
            set_title_bar_color(self, True)
            # Drain layout/native paint only; application timers stay queued
            # until the window has been revealed to the normal main loop.
            if not paint_window_now(self, max_tk_events=48):
                self._abort_initial_show(generation)
                return
            if target_geometry is not None:
                self.geometry(target_geometry)
                if gated:
                    set_native_window_alpha(self, 0.0)
                if getattr(self, '_repaint_after_move', False):
                    if not paint_window_now(
                        self, max_tk_events=24, max_native_messages=256
                    ):
                        self._abort_initial_show(generation)
                        return
                else:
                    self.update_idletasks()
        except TclError:
            self._abort_initial_show(generation)
            return
        if not _window_exists(self):
            self._abort_initial_show(generation)
            return
        self._finish_initial_show(generation)

    def _finish_initial_show(self, generation: int | None = None) -> None:
        generation = self._initial_show_generation if generation is None else generation
        if generation != self._initial_show_generation:
            return
        if self._initial_show_complete or not _window_exists(self):
            if not self._initial_show_complete:
                self._abort_initial_show(generation)
            return
        try:
            if self._focus_on_open:
                # Native ownership was fixed while withdrawn; only foreground
                # activation is deferred until the hidden client paint is done.
                self.present_in_foreground()
                if not _window_exists(self):
                    self._abort_initial_show(generation)
                    return
            target_alpha = current_window_alpha()
            self.attributes("-alpha", target_alpha)
            set_native_window_alpha(self, target_alpha)
            set_native_window_cloaked(self, False)
            _flush_desktop_compositor()
        except (RuntimeError, TclError):
            self._abort_initial_show(generation)
            return
        self._appearance_alpha_gated = False
        self._initial_show_in_progress = False
        self._initial_show_complete = True

    def _abort_initial_show(self, generation: int) -> None:
        if generation != self._initial_show_generation:
            return
        self._initial_show_generation += 1
        self._initial_show_scheduled = False
        self._initial_show_in_progress = False
        if _window_exists(self):
            try:
                TkToplevel.withdraw(self)
                target_alpha = current_window_alpha()
                self.attributes("-alpha", target_alpha)
                set_native_window_alpha(self, target_alpha)
                set_native_window_cloaked(self, False)
            except (AttributeError, TclError):
                pass
        self._appearance_alpha_gated = False

    def deiconify(self) -> None:
        if not self._initial_show_complete:
            if self._auto_show:
                self._schedule_initial_show()
            elif not self._initial_show_in_progress:
                # Manually controlled windows (currently the startup splash)
                # still need the same first-Map gate.  They are expected to be
                # ready when deiconify() returns, so finish their one paint
                # synchronously instead of waiting for the normal timer.
                self._show_when_ready()
                if self._initial_show_in_progress:
                    self._finish_initial_show(self._initial_show_generation)
            return
        TkToplevel.deiconify(self)

    wm_deiconify = deiconify

    def _on_window_mapped(self, event: tk.Event) -> None:
        # Tk can deliver descendant widget map events through the toplevel bind tag.
        # Only the actual window map event may trigger foreground presentation.
        if event.widget is not self:
            return
        if self._initial_show_complete:
            self._schedule_foreground_presentation()

    def _schedule_foreground_presentation(self) -> None:
        if (
            not self._focus_on_open
            or self._foreground_scheduled
            or self._foreground_presented
        ):
            return
        self._foreground_scheduled = True
        self.after(0, self._present_scheduled_window)

    def _present_scheduled_window(self) -> None:
        self._foreground_scheduled = False
        self.present_in_foreground()

    def present_in_foreground(self, *, force: bool = False) -> None:
        if self._foreground_presented and not force:
            return
        if present_window(
            self,
            owner=self._window_owner,
            transient=False,
        ):
            self._foreground_presented = True

    def center_after_layout(self, *, force: bool = False) -> None:
        if not self._initial_show_complete:
            self._center_on_open = True
            if force:
                self._centered_once = False
            return
        self.after(0, lambda: self.center_on_screen(force=force))

    def center_on_screen(self, *, force: bool = False) -> None:
        if self._centered_once and not force:
            return
        try:
            from src.ui.common.geometry import move_center

            move_center(self)
        except (TclError, RuntimeError):
            return
        self._centered_once = True


__all__ = [
    "CustomControls",
    "Toplevel",
    "present_window",
    "register_main_window",
    "resolve_window_owner",
]
