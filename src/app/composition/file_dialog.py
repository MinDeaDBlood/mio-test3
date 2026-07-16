from __future__ import annotations

import logging

from src.app.file_dialog_controller import FileDialogController
from src.app.file_dialog_paths import (
    accept_directory_target,
    accept_file_target,
    initial_directory,
    resolve_directory_activation,
    resolve_file_activation,
)
from src.app.localization_runtime import lang
from src.app.composition import file_dialog_keys as keys
from src.app.ui_feedback import build_ui_dispatcher
from src.app.ui_tasks import build_ui_task_runner
from src.ui.common.mkc_filedialog import DirectorySelectionDialog, FileSelectionDialog


def _controller_for(window) -> FileDialogController:
    dispatcher = build_ui_dispatcher(host_window=window)
    runner = build_ui_task_runner(
        dispatcher=dispatcher, is_alive=window.winfo_exists, logger=logging
    )
    return FileDialogController(runner)


def choose_file(
    *, title: str | None = None, filetypes=(("*", "*.*"),), **_kwargs
) -> str:
    window = FileSelectionDialog(
        texts=lang,
        title=title or lang.resolve_required_ui_text(keys.DEFAULT_FILE_DIALOG_TITLE),
        filetypes=tuple(filetypes),
        initial_directory=initial_directory(),
        resolve_activation=resolve_file_activation,
        accept_target=accept_file_target,
        refresh_files=lambda *_args, **_kwargs: None,
        show_error=lambda message: logging.error(
            "file_dialog.list_failed: %s", message
        ),
    )
    controller = _controller_for(window)
    window._refresh_files = controller.refresh_files
    window.refresh_entries()
    window.center_on_screen(force=True)
    window.wait_window()
    return window.file


def choose_directory(*, title: str | None = None, **_kwargs) -> str:
    window = DirectorySelectionDialog(
        texts=lang,
        title=title
        or lang.resolve_required_ui_text(keys.DEFAULT_DIRECTORY_DIALOG_TITLE),
        initial_directory=initial_directory(),
        resolve_activation=resolve_directory_activation,
        accept_target=accept_directory_target,
        refresh_directories=lambda *_args, **_kwargs: None,
        show_error=lambda message: logging.error(
            "directory_dialog.list_failed: %s", message
        ),
    )
    controller = _controller_for(window)
    window._refresh_directories = controller.refresh_directories
    window.refresh_entries()
    window.center_on_screen(force=True)
    window.wait_window()
    return window.file


__all__ = ["choose_directory", "choose_file"]
