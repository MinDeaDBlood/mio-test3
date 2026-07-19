"""Notebook-compatible tab stack that never exposes a partially mapped page."""

from __future__ import annotations

import tkinter as tk
from tkinter import TclError, ttk
from typing import Any

class BufferedNotebook(ttk.Frame):
    """Small subset of ttk.Notebook used by MIO Kitchen.

    Before a selection is raised, ``<<NotebookTabChanging>>`` gives lazy hosts
    a chance to build the target.  It is then mapped beneath the current page,
    fully laid out there, and published with one final ``tkraise`` operation.
    """

    def __init__(self, master: tk.Misc, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)
        self._tab_bar = ttk.Frame(self)
        self._tab_bar.grid(row=0, column=0, sticky='ew')
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self._tabs: list[tk.Misc] = []
        self._buttons: dict[str, ttk.Radiobutton] = {}
        self._selected: tk.Misc | None = None
        self._pending: tk.Misc | None = None
        self._buffered_pages: set[tk.Misc] = set()
        self._buffered_focus: dict[tk.Misc, object] = {}
        self._selection_var = tk.StringVar(master=self)

    def add(self, child: tk.Misc, *, text: str = '', **_kwargs: Any) -> None:
        if child in self._tabs:
            return
        child.grid(row=1, column=0, sticky='nsew')
        tab_id = str(child)
        button = ttk.Radiobutton(
            self._tab_bar,
            text=text,
            value=tab_id,
            variable=self._selection_var,
            style='Toolbutton',
            command=lambda tab=child: self.select(tab),
        )
        button.pack(side='left', fill='x')
        button.bind('<Left>', lambda _event, tab=child: self._select_relative(tab, -1))
        button.bind('<Right>', lambda _event, tab=child: self._select_relative(tab, 1))
        self._tabs.append(child)
        self._buttons[tab_id] = button
        if self._selected is None:
            self._selected = child
            self._selection_var.set(tab_id)
        else:
            child.grid_remove()

    def tabs(self) -> tuple[str, ...]:
        return tuple(str(tab) for tab in self._tabs)

    def select(self, tab_id: object | None = None) -> str:
        if tab_id is None:
            return str(self._selected) if self._selected is not None else ''

        target = self._resolve_tab(tab_id)
        if target is self._selected:
            return str(target)

        self._pending = target
        self.event_generate('<<NotebookTabChanging>>', when='now')
        previous = self._selected
        focused = self.focus_get()
        focus_was_on_previous = (
            previous is not None and self._is_within_page(focused, previous)
        )
        target.grid(row=1, column=0, sticky='nsew')
        if previous is not None:
            target.lower(previous)
        # Lazy handlers have populated the target. Tk will not service its
        # pending paint until this selection callback returns, so publish the
        # final stacking state directly instead of draining every idle task in
        # the application on each tab click.
        self._set_page_focusability(target, enabled=True)
        target.tkraise()
        if previous is not None:
            if previous in self._buffered_pages:
                self._set_page_focusability(previous, enabled=False)
                previous.lower(target)
            else:
                previous.grid_remove()
        self._selected = target
        self._selection_var.set(str(target))
        self._pending = None
        if focus_was_on_previous:
            try:
                self._buttons[str(target)].focus_set()
            except (KeyError, TclError):
                pass
        self.event_generate('<<NotebookTabChanged>>', when='now')
        return str(target)

    def selection_target(self) -> str:
        target = self._pending if self._pending is not None else self._selected
        return str(target) if target is not None else ''

    def buffer_page(self, tab_id: object) -> None:
        """Keep a costly page painted beneath the active page for instant reveal."""
        target = self._resolve_tab(tab_id)
        self._buffered_pages.add(target)
        if target is self._selected:
            return
        self._set_page_focusability(target, enabled=False)
        target.grid(row=1, column=0, sticky='nsew')
        if self._selected is not None:
            target.lower(self._selected)
        target.update_idletasks()

    def refresh_focusability(self) -> None:
        """Compatibility hook; only the selected page is geometry-managed."""

    def invalidate_focusability(self, page: tk.Misc) -> None:
        """Compatibility hook for lazily populated pages."""
        del page

    def _set_page_focusability(self, page: tk.Misc, *, enabled: bool) -> None:
        stack = [page]
        while stack:
            widget = stack.pop()
            try:
                stack.extend(widget.winfo_children())
                current = widget.cget('takefocus')
            except (AttributeError, TclError):
                continue
            if enabled:
                if widget in self._buffered_focus:
                    widget.configure(takefocus=self._buffered_focus.pop(widget))
            else:
                if widget not in self._buffered_focus:
                    self._buffered_focus[widget] = current
                widget.configure(takefocus=0)

    def _resolve_tab(self, tab_id: object) -> tk.Misc:
        if isinstance(tab_id, int):
            return self._tabs[tab_id]
        if isinstance(tab_id, tk.Misc) and tab_id in self._tabs:
            return tab_id  # type: ignore[return-value]
        text = str(tab_id)
        for tab in self._tabs:
            if str(tab) == text:
                return tab
        raise TclError(f'Unknown tab {tab_id!r}')

    def _select_relative(self, current: tk.Misc, delta: int) -> str:
        index = self._tabs.index(current)
        target = self._tabs[(index + delta) % len(self._tabs)]
        self.select(target)
        self._buttons[str(target)].focus_set()
        return 'break'

    @staticmethod
    def _is_within_page(widget: tk.Misc | None, page: tk.Misc) -> bool:
        current = widget
        while current is not None:
            if current is page:
                return True
            current = getattr(current, 'master', None)
        return False


__all__ = ['BufferedNotebook']
