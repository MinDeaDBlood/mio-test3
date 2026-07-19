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
from time import monotonic
from tkinter import ttk

from tests.support.runtime_smoke import lang, prepare_root
from src.ui.tabs.tools.download_firmware import keys as download_keys
from src.ui.tabs.tools.toolbox import _TOOL_SPECS


def iter_widgets(widget):
    for child in widget.winfo_children():
        yield child
        yield from iter_widgets(child)


def find_button(root, text: str) -> ttk.Button:
    for widget in iter_widgets(root):
        if isinstance(widget, ttk.Button) and str(widget.cget("text")) == text:
            return widget
    raise AssertionError(f"Button not found: {text!r}")


def submit_empty_url(root, *, deadline: float, callback_errors) -> None:
    try:
        title = lang.resolve_required_ui_text(download_keys.URL_DIALOG_TITLE)
        frames = [
            widget
            for widget in iter_widgets(root)
            if isinstance(widget, ttk.LabelFrame) and widget.cget("text") == title
        ]
        if not frames:
            assert monotonic() < deadline, "Firmware URL prompt did not open"
            root.after(
                10,
                lambda: submit_empty_url(
                    root,
                    deadline=deadline,
                    callback_errors=callback_errors,
                ),
            )
            return
        frame = frames[-1]
        entry = next(
            child for child in frame.winfo_children() if isinstance(child, ttk.Entry)
        )
        assert entry.get() == ""
        button = next(
            child for child in frame.winfo_children() if isinstance(child, ttk.Button)
        )
        button.invoke()
    except BaseException as exc:
        callback_errors.append(exc)
        raise


def accept_validation_dialog(
    root,
    *,
    deadline: float,
    callback_errors,
    validation_messages: list[str],
) -> None:
    try:
        dialogs = [
            widget
            for widget in root.winfo_children()
            if isinstance(widget, tk.Toplevel) and widget.winfo_exists()
        ]
        expected = lang.resolve_required_ui_text(download_keys.EMPTY_URL_MESSAGE)
        for dialog in dialogs:
            labels = [
                widget
                for widget in iter_widgets(dialog)
                if isinstance(widget, ttk.Label)
            ]
            if not any(label.cget("text") == expected for label in labels):
                continue
            validation_messages.append(expected)
            button = next(
                widget
                for widget in iter_widgets(dialog)
                if isinstance(widget, ttk.Button)
            )
            button.invoke()
            return
        assert monotonic() < deadline, "Empty-URL validation dialog did not open"
        root.after(
            10,
            lambda: accept_validation_dialog(
                root,
                deadline=deadline,
                callback_errors=callback_errors,
                validation_messages=validation_messages,
            ),
        )
    except BaseException as exc:
        callback_errors.append(exc)
        raise


def current_toplevels(root) -> dict[str, tk.Toplevel]:
    return {
        str(widget): widget
        for widget in root.winfo_children()
        if isinstance(widget, tk.Toplevel) and widget.winfo_exists()
    }


def main() -> None:
    root = prepare_root()
    callback_errors: list[BaseException] = []
    validation_messages: list[str] = []
    root.report_callback_exception = (
        lambda _kind, error, _traceback: callback_errors.append(error)
    )
    try:
        for localization_key, opener_id in _TOOL_SPECS:
            button_text = lang.resolve(localization_key, default="")
            assert button_text, (
                f"Missing localization for toolbox button: {localization_key}"
            )
            button = find_button(root, button_text)
            before = current_toplevels(root)
            callback_errors.clear()
            if opener_id == "download_firmware":
                deadline = monotonic() + 5.0
                root.after(
                    10,
                    lambda: submit_empty_url(
                        root,
                        deadline=deadline,
                        callback_errors=callback_errors,
                    ),
                )
                root.after(
                    10,
                    lambda: accept_validation_dialog(
                        root,
                        deadline=deadline,
                        callback_errors=callback_errors,
                        validation_messages=validation_messages,
                    ),
                )
            button.invoke()
            root.update()
            assert callback_errors == [], (
                f"{opener_id} callback failed: {callback_errors!r}"
            )

            after = current_toplevels(root)
            created = [window for path, window in after.items() if path not in before]
            if opener_id == "download_firmware":
                assert validation_messages[-1:] == [
                    lang.resolve_required_ui_text(download_keys.EMPTY_URL_MESSAGE)
                ]
                assert created == []
            else:
                assert created, f"{opener_id} did not create its tool window"

            for window in created:
                if window.winfo_exists():
                    window.destroy()
            root.update_idletasks()
    finally:
        for widget in list(root.winfo_children()):
            if isinstance(widget, tk.Toplevel) and widget.winfo_exists():
                widget.destroy()
        root.destroy()

    print("TOOLBOX_CLICK_SMOKE_OK")


if __name__ == "__main__":
    main()
