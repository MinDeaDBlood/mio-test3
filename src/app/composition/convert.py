from __future__ import annotations

from src.app.localization_runtime import lang
import logging
from tkinter import TclError

from src.app.project_contexts import build_app_convert_context
from src.app.projects.convert.controller import ConvertController
from src.logic.projects.convert.models import INPUT_FORMATS, OUTPUT_FORMATS
from src.app.ui_feedback import build_ui_dispatcher
from src.app.ui_tasks import build_ui_task_runner
from src.app.composition.service_output import build_ui_service_output
from src.ui.tabs.project.convert.frame import FormatConversion

_conversion_window = None


def _clear_conversion_window(window):
    global _conversion_window
    if _conversion_window is window:
        _conversion_window = None


def _is_live(window) -> bool:
    try:
        return bool(window is not None and window.winfo_exists())
    except (TclError, RuntimeError):
        return False


def open_conversion_window(*, master=None):
    global _conversion_window
    if _is_live(_conversion_window):
        _conversion_window.deiconify()
        _conversion_window.lift()
        try:
            _conversion_window.focus_set()
        except (TclError, RuntimeError):
            pass
        return _conversion_window

    window = FormatConversion(
        master=master,
        texts=lang,
        controller=ConvertController(
            build_app_convert_context(output=build_ui_service_output(texts=lang))
        ),
        input_formats=INPUT_FORMATS,
        output_formats=OUTPUT_FORMATS,
        task_runner_factory=lambda host: build_ui_task_runner(
            dispatcher=build_ui_dispatcher(host_window=host),
            is_alive=host.winfo_exists,
            logger=logging,
        ),
    )
    _conversion_window = window
    window.bind(
        "<Destroy>",
        lambda event, created=window: _clear_conversion_window(created)
        if event.widget is created
        else None,
        add="+",
    )
    return window


__all__ = ["open_conversion_window"]
