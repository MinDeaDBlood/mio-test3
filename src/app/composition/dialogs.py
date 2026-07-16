from __future__ import annotations

from importlib import import_module
from typing import Any
import os

from src.app.localization_runtime import lang


def _warn_dialogs() -> Any:
    return import_module('src.ui.warn.dialogs')


def ask_win(*args: Any, **kwargs: Any) -> Any:
    kwargs.setdefault('texts', lang)
    return _warn_dialogs().ask_win(*args, **kwargs)


def info_win(*args: Any, **kwargs: Any) -> Any:
    kwargs.setdefault('texts', lang)
    return _warn_dialogs().info_win(*args, **kwargs)


def warn_win(*args: Any, **kwargs: Any) -> Any:
    kwargs.setdefault('texts', lang)
    return _warn_dialogs().warn_win(*args, **kwargs)


def choose_file(*args: Any, **kwargs: Any) -> str:
    if os.name == 'nt':
        return import_module('tkinter.filedialog').askopenfilename(*args, **kwargs)
    return import_module('src.app.composition.file_dialog').choose_file(*args, **kwargs)


def choose_directory(*args: Any, **kwargs: Any) -> str:
    if os.name == 'nt':
        return import_module('tkinter.filedialog').askdirectory(*args, **kwargs)
    return import_module('src.app.composition.file_dialog').choose_directory(*args, **kwargs)


__all__ = ['ask_win', 'info_win', 'warn_win', 'choose_file', 'choose_directory']
