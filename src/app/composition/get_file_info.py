from __future__ import annotations

from src.app.composition.dialogs import choose_file
from src.app.localization_runtime import lang
from src.app.tools.get_file_info_controller import GetFileInfoController
from src.core.byte_size import format_bytes
from src.core.file_types import gettype
from src.ui.tabs.tools.get_file_info import keys
from src.ui.tabs.tools.get_file_info.window import GetFileInfo


def open_get_file_info_window() -> GetFileInfo:
    text = lang.resolve_required_ui_text
    return GetFileInfo(
        language=lang,
        controller=GetFileInfoController(gettype_func=gettype),
        choose_file=lambda: choose_file(
            title=text(keys.FILE_DIALOG_TITLE),
            filetypes=((text(keys.FILE_DIALOG_ALL_FILES), "*.*"),),
        ),
        human_size=format_bytes,
    )


__all__ = ["open_get_file_info_window"]
