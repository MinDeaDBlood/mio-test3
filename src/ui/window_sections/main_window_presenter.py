from __future__ import annotations

from dataclasses import dataclass
import os
import time

from src.ui.common.formatting import enum_value
from src.ui.window_sections import main_window_presenter_keys as keys


@dataclass(frozen=True)
class StartupWarning:
    message: str


def render_startup_warning(code: object, *, texts) -> StartupWarning | None:
    value = str(enum_value(code))
    if value == "non-root-posix":
        return StartupWarning(
            texts.resolve_required_ui_text(keys.NON_ROOT_POSIX_WARNING)
        )
    if value == "loongarch64":
        return StartupWarning(texts.resolve_required_ui_text(keys.LOONGARCH64_WARNING))
    return None


def current_clock_text() -> str:
    return time.strftime("%H:%M:%S")


def safe_initial_alpha(window, logger=None) -> float:
    initial_alpha = 1.0
    try:
        window.update_idletasks()
        initial_alpha = float(window.attributes("-alpha"))
        if logger:
            logger.info("Tool.__init__: Initial alpha detected as %s", initial_alpha)
    except Exception as exc:
        if logger:
            logger.warning(
                "Tool.__init__: Could not get initial alpha (%s), assuming %s.",
                exc,
                initial_alpha,
            )
    return initial_alpha


def apply_windows_font_fix(window, *, logger=None, do_set_window_deffont=None) -> None:
    if os.name == "nt" and callable(do_set_window_deffont):
        try:
            do_set_window_deffont(window)
        except Exception as exc:
            if logger:
                logger.error("Tool.__init__: Error in do_set_window_deffont: %s", exc)


def apply_windows_alpha_fix(window, *, initial_alpha: float, logger=None) -> None:
    if os.name != "nt":
        return
    try:
        if logger:
            logger.info("Tool.__init__: Applying alpha shake fix for Windows.")
        window.attributes("-alpha", 0.99)
        window.update_idletasks()
        window.attributes("-alpha", initial_alpha)
        window.update_idletasks()
    except Exception as exc:
        if logger:
            logger.error("Tool.__init__: Error during alpha shake fix: %s", exc)
