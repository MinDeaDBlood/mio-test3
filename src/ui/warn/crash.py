from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
import tkinter as tk
from tkinter import BOTH, LEFT, Label, Text, ttk

import sv_ttk

from src.ui.common.geometry import move_center
from src.ui.warn.common import themed_toplevel
from src.ui.warn.models import CrashContext
from src.ui.localization import LocalizationCatalog
from src.ui.warn import crash_keys as keys


@dataclass(frozen=True)
class CrashWindowActions:
    generate_bug_report: Callable[[], object]
    restart: Callable[[object], object]
    exit_application: Callable[[], object]
    open_issue_tracker: Callable[[], object]
    create_stdout_sink: Callable[[Text], object]
    create_stderr_sink: Callable[[Text], object]


@lru_cache(maxsize=1)
def _resolve_error_logo_helpers():
    from PIL.Image import open as open_img
    from PIL.ImageTk import PhotoImage
    from src.ui.assets.images import error_logo

    return open_img, PhotoImage, error_logo


def build_crash_window(
    context: CrashContext,
    *,
    root_window,
    version: str,
    tool_log: str,
    actions: CrashWindowActions,
    texts: LocalizationCatalog,
):
    """Build and display the crash view from explicit application inputs."""
    sv_ttk.use_dark_theme()
    window = themed_toplevel(parent=root_window)
    open_img, PhotoImage, error_logo = _resolve_error_logo_helpers()
    image = open_img(BytesIO(error_logo)).resize((100, 100))
    photo = PhotoImage(image)
    label = Label(window, image=photo)
    label.image = photo
    label.pack(padx=10, pady=10)
    window.protocol("WM_DELETE_WINDOW", actions.exit_application)
    window.title(
        texts.resolve_required_ui_text(keys.TITLE_FORMAT).format(version=version)
    )
    window.lift()

    ttk.Label(
        window,
        text=texts.resolve_required_ui_text(keys.ERROR_CODE_FORMAT).format(
            code=context.code
        ),
        font=(None, 20),
        foreground="red",
    ).pack(padx=10, pady=10)
    ttk.Label(
        window,
        text=texts.resolve_required_ui_text(keys.GUIDANCE),
        font=(None, 10),
    ).pack(padx=10, pady=10)

    scrollbar = ttk.Scrollbar(window)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text_widget = Text(window, height=20, width=60)
    stdout_sink = actions.create_stdout_sink(text_widget)
    stderr_sink = actions.create_stderr_sink(text_widget)
    window._stdout_sink = stdout_sink
    window._stderr_sink = stderr_sink
    scrollbar.config(command=text_widget.yview)
    text_widget.pack(padx=10, pady=10, fill=BOTH)
    text_widget.insert("insert", context.description)
    text_widget.config(yscrollcommand=scrollbar.set)

    ttk.Label(
        window,
        text=texts.resolve_required_ui_text(keys.LOG_PATH_FORMAT).format(path=tool_log),
        font=(None, 10),
    ).pack(padx=10, pady=10)
    ttk.Button(
        window,
        text=texts.resolve_required_ui_text(keys.REPORT),
        command=actions.open_issue_tracker,
        style="Accent.TButton",
    ).pack(side=LEFT, padx=10, pady=10, expand=True, fill=BOTH)
    ttk.Button(
        window,
        text=texts.resolve_required_ui_text(keys.GENERATE_BUG_REPORT),
        command=actions.generate_bug_report,
        style="Accent.TButton",
    ).pack(side=LEFT, padx=10, pady=10, expand=True, fill=BOTH)
    ttk.Button(
        window,
        text=texts.resolve_required_ui_text(keys.RESTART),
        command=lambda: actions.restart(window),
        style="Accent.TButton",
    ).pack(side=LEFT, padx=10, pady=10, expand=True, fill=BOTH)
    ttk.Button(
        window,
        text=texts.resolve_required_ui_text(keys.EXIT),
        command=actions.exit_application,
    ).pack(side=LEFT, padx=10, pady=10, expand=True, fill=BOTH)
    move_center(window)
    return window


__all__ = ["CrashWindowActions", "build_crash_window"]
