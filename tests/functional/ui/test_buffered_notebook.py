from __future__ import annotations

# Direct file execution bootstrap
import sys as _direct_sys
from pathlib import Path as _DirectPath

_DIRECT_PROJECT_ROOT = _DirectPath(__file__).resolve().parent
while _DIRECT_PROJECT_ROOT != _DIRECT_PROJECT_ROOT.parent:
    if (
        (_DIRECT_PROJECT_ROOT / "src").is_dir()
        and (_DIRECT_PROJECT_ROOT / "tests").is_dir()
        and (_DIRECT_PROJECT_ROOT / "scripts").is_dir()
    ):
        break
    _DIRECT_PROJECT_ROOT = _DIRECT_PROJECT_ROOT.parent
else:
    raise RuntimeError(f"Project root was not found for {__file__}")

_direct_root_text = str(_DIRECT_PROJECT_ROOT)
if _direct_root_text not in _direct_sys.path:
    _direct_sys.path.insert(0, _direct_root_text)
if __package__ in {None, ""}:
    _direct_relative = _DirectPath(__file__).resolve().relative_to(
        _DIRECT_PROJECT_ROOT
    ).with_suffix("")
    __package__ = ".".join(_direct_relative.parts[:-1])


import tkinter as tk
from tkinter import ttk

import pytest

from src.ui.common.buffered_notebook import BufferedNotebook


def _create_root() -> tk.Tk:
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk display is unavailable: {exc}")
    root.withdraw()
    return root


def test_target_is_available_to_lazy_handlers_before_selection_changes() -> None:
    root = _create_root()
    try:
        notebook = BufferedNotebook(root)
        current = ttk.Frame(notebook)
        target = ttk.Frame(notebook)
        notebook.add(current, text="Current")
        notebook.add(target, text="Target")
        notebook.pack()

        observed: list[tuple[str, str]] = []
        notebook.bind(
            "<<NotebookTabChanging>>",
            lambda _event: observed.append(
                (notebook.select(), notebook.selection_target())
            ),
        )

        notebook.select(target)

        assert observed == [(str(current), str(target))]
        assert notebook.select() == str(target)
    finally:
        root.destroy()


def test_only_active_page_is_managed_and_accepts_focus() -> None:
    root = _create_root()
    try:
        notebook = BufferedNotebook(root)
        first = ttk.Frame(notebook)
        second = ttk.Frame(notebook)
        first_entry = ttk.Entry(first)
        second_entry = ttk.Entry(second)
        first_entry.pack()
        second_entry.pack()
        notebook.add(first, text="First")
        notebook.add(second, text="Second")
        notebook.pack()
        notebook.refresh_focusability()

        assert first.winfo_manager() == "grid"
        assert second.winfo_manager() == ""
        assert first_entry.cget("takefocus") == "ttk::takefocus"
        assert not second_entry.winfo_viewable()

        notebook.select(second)

        assert first.winfo_manager() == ""
        assert second.winfo_manager() == "grid"
        assert not first_entry.winfo_viewable()
        assert second_entry.cget("takefocus") == "ttk::takefocus"
    finally:
        root.destroy()


def test_buffered_page_stays_painted_but_cannot_take_focus_until_selected() -> None:
    root = _create_root()
    try:
        notebook = BufferedNotebook(root)
        first = ttk.Frame(notebook)
        second = ttk.Frame(notebook)
        second_entry = ttk.Entry(second)
        second_entry.pack()
        notebook.add(first, text="First")
        notebook.add(second, text="Second")
        notebook.pack()

        notebook.buffer_page(second)

        assert second.winfo_manager() == "grid"
        assert str(second_entry.cget("takefocus")) == "0"

        notebook.select(second)
        assert second_entry.cget("takefocus") == "ttk::takefocus"

        notebook.select(first)
        assert second.winfo_manager() == "grid"
        assert str(second_entry.cget("takefocus")) == "0"
    finally:
        root.destroy()


if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
