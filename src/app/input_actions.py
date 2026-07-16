from __future__ import annotations

from collections.abc import Iterable

from src.app.composition.dialogs import choose_file
from src.app.file_drop import InputPathDispatchResult, handle_input_paths
from src.app.localization_runtime import lang
from src.app import input_actions_keys as keys


def dispatch_input_paths(files: Iterable[str]) -> InputPathDispatchResult:
    result = handle_input_paths(files)
    for path in result.missing_paths:
        print(path + lang.resolve_required_ui_text(keys.PATH_NOT_FOUND_SUFFIX))
    return result


def choose_and_dispatch_input_file() -> InputPathDispatchResult:
    path = choose_file()
    if not path:
        return InputPathDispatchResult()
    return dispatch_input_paths([path])


__all__ = ["choose_and_dispatch_input_file", "dispatch_input_paths"]
