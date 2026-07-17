"""Application managed startup splash shown only after file logging is active."""
from __future__ import annotations

import logging
import platform
from pathlib import Path
import sys
from typing import Any

logger = logging.getLogger(__name__)


def _resolve_splash_asset() -> Path | None:
    candidates: list[Path] = []
    bundle_root = sys._MEIPASS if hasattr(sys, '_MEIPASS') else None
    preferred_name = (
        'splash_loongarch.png'
        if platform.system() == 'Linux' and platform.machine().lower() == 'loongarch64'
        else 'splash.png'
    )
    if bundle_root:
        candidates.append(Path(bundle_root) / preferred_name)
        candidates.append(Path(bundle_root) / 'splash.png')
    source_root = Path(__file__).resolve().parents[2]
    candidates.append(source_root / preferred_name)
    candidates.append(source_root / 'splash.png')
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


class StartupSplash:
    """Borderless splash tied to the already created Tk application root."""

    def __init__(self, main_window: Any, image_path: Path) -> None:
        from tkinter import Label
        from PIL import Image, ImageTk
        from src.ui.common.windowing import Toplevel

        self._main_window = main_window
        self._window = Toplevel(
            main_window,
            center_on_open=False,
            focus_on_open=False,
        )
        self._window.withdraw()
        self._window.overrideredirect(True)
        try:
            self._window.attributes('-topmost', True)
        except Exception:
            logger.debug('The platform does not support a topmost startup splash')

        with Image.open(image_path) as source:
            image = source.convert('RGBA')
            screen_width = max(1, int(self._window.winfo_screenwidth()))
            screen_height = max(1, int(self._window.winfo_screenheight()))
            scale = min(
                1.0,
                (screen_width * 0.90) / image.width,
                (screen_height * 0.80) / image.height,
            )
            if scale < 1.0:
                target = (
                    max(1, int(image.width * scale)),
                    max(1, int(image.height * scale)),
                )
                image = image.resize(target, Image.Resampling.LANCZOS)
            self._photo = ImageTk.PhotoImage(image, master=self._window)

        label = Label(
            self._window,
            image=self._photo,
            borderwidth=0,
            highlightthickness=0,
        )
        label.pack()
        self._window.update_idletasks()
        width = self._photo.width()
        height = self._photo.height()
        x = max(0, (self._window.winfo_screenwidth() - width) // 2)
        y = max(0, (self._window.winfo_screenheight() - height) // 2)
        self._window.geometry(f'{width}x{height}+{x}+{y}')
        self._main_window.withdraw()
        self._window.deiconify()
        self._window.lift()
        self._window.update_idletasks()
        self._window.update()
        logger.info('Application startup splash displayed: %s', image_path)

    def close(self) -> None:
        try:
            if self._window.winfo_exists():
                self._window.destroy()
        except Exception:
            logger.exception('Unable to close the application startup splash')
        finally:
            try:
                self._main_window.deiconify()
                self._main_window.lift()
                self._main_window.update_idletasks()
            except Exception:
                logger.exception('Unable to reveal the main window after startup')
        logger.info('Application startup splash closed')


def show_startup_splash(main_window: Any) -> StartupSplash | None:
    image_path = _resolve_splash_asset()
    if image_path is None:
        logger.warning('Startup splash asset was not found')
        return None
    try:
        return StartupSplash(main_window, image_path)
    except Exception:
        logger.exception('Unable to display the application startup splash')
        return None


__all__ = ['StartupSplash', 'show_startup_splash']
