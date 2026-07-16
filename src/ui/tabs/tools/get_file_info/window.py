from __future__ import annotations

import logging
from collections.abc import Callable
from tkinter import BOTH, TOP, X, Frame, ttk

from src.ui.common.windowing import Toplevel
from src.ui.contracts import GetFileInfoControllerPort
from src.ui.tabs.tools.get_file_info import keys


class GetFileInfo(Toplevel):
    def __init__(
        self,
        *,
        language,
        controller: GetFileInfoControllerPort,
        choose_file: Callable[..., str],
        human_size: Callable[[int], str],
    ) -> None:
        super().__init__()
        self._language = language
        self._controller = controller
        self._choose_file = choose_file
        self._human_size = human_size
        self.controls = []
        self.title(self._text(keys.TITLE))
        self._build_ui()
        self.geometry("400x450")
        self.center_on_screen(force=True)

    def _text(self, key: str) -> str:
        return self._language.resolve_required_ui_text(key)

    def _build_ui(self) -> None:
        from src.ui.common.dnd import DND_FILES

        drop_frame = ttk.LabelFrame(self, text=self._text(keys.DROP_GROUP_TITLE))
        drop_label = ttk.Label(drop_frame, text=self._text(keys.DROP_HINT))
        drop_label.pack(fill=BOTH, padx=5, pady=5)
        drop_label.bind(
            "<Button-1>", lambda *_args: self.start_dnd([self._choose_file()])
        )
        drop_frame.pack(side=TOP, padx=5, pady=5, fill=BOTH)
        drop_frame.drop_target_register(DND_FILES)
        drop_frame.dnd_bind("<<Drop>>", lambda event: self.start_dnd([event.data]))
        self.info_frame = ttk.LabelFrame(
            self,
            text=self._text(keys.INFORMATION_GROUP_TITLE),
        )
        self.info_frame.pack(fill=BOTH, side=TOP)

    def put_info(
        self,
        name: str,
        value,
        *,
        copy_text: str,
        copied_text: str,
    ) -> None:
        frame = Frame(self.info_frame)
        self.controls.append(frame)
        ttk.Label(frame, text=f"{name}:", width=7).pack(fill=X, side="left")
        entry = ttk.Entry(frame)
        entry.insert(0, value)
        entry.pack(fill=X, side="left", padx=5, pady=5, expand=True)
        button = ttk.Button(frame, text=copy_text)
        button.configure(
            command=lambda: self.copy_to_clipboard(
                entry.get(),
                button,
                copy_text=copy_text,
                copied_text=copied_text,
            )
        )
        button.pack(fill=X, side="left", padx=5, pady=5)
        frame.pack(fill=X)

    def copy_to_clipboard(
        self,
        value,
        button: ttk.Button,
        *,
        copy_text: str,
        copied_text: str,
    ) -> None:
        button.configure(text=copied_text, state="disabled")
        self.clipboard_clear()
        self.clipboard_append(value)
        button.after(
            1500,
            lambda: button.configure(text=copy_text, state="normal"),
        )

    def clear(self) -> None:
        for control in self.controls:
            try:
                control.destroy()
            except Exception:
                logging.exception("Unable to destroy file-info control: %r", control)
        self.controls.clear()

    def _row(
        self,
        label_key: str,
        value,
        copy_key: str,
        copied_key: str,
    ) -> tuple[str, object, str, str]:
        return (
            self._text(label_key),
            value,
            self._text(copy_key),
            self._text(copied_key),
        )

    def start_dnd(self, file_list) -> bool | None:
        file = self._controller.normalize_file(file_list)
        self.clear()
        self.deiconify()
        self.lift()
        self.focus_force()
        info = self._controller.read_info(file)
        if info is None:
            row = self._row(
                keys.MISSING_FILE_ROW_LABEL,
                self._text(keys.MISSING_FILE_MESSAGE),
                keys.MISSING_FILE_COPY_BUTTON,
                keys.MISSING_FILE_COPIED_BUTTON,
            )
            self.put_info(row[0], row[1], copy_text=row[2], copied_text=row[3])
            return None
        rows = (
            self._row(
                keys.NAME_ROW_LABEL,
                info.name,
                keys.NAME_COPY_BUTTON,
                keys.NAME_COPIED_BUTTON,
            ),
            self._row(
                keys.PATH_ROW_LABEL,
                info.path,
                keys.PATH_COPY_BUTTON,
                keys.PATH_COPIED_BUTTON,
            ),
            self._row(
                keys.TYPE_ROW_LABEL,
                info.file_type,
                keys.TYPE_COPY_BUTTON,
                keys.TYPE_COPIED_BUTTON,
            ),
            self._row(
                keys.HUMAN_SIZE_ROW_LABEL,
                self._human_size(info.size_bytes),
                keys.HUMAN_SIZE_COPY_BUTTON,
                keys.HUMAN_SIZE_COPIED_BUTTON,
            ),
            self._row(
                keys.BYTE_SIZE_ROW_LABEL,
                info.size_bytes,
                keys.BYTE_SIZE_COPY_BUTTON,
                keys.BYTE_SIZE_COPIED_BUTTON,
            ),
            self._row(
                keys.CREATED_TIME_ROW_LABEL,
                info.created_time,
                keys.CREATED_TIME_COPY_BUTTON,
                keys.CREATED_TIME_COPIED_BUTTON,
            ),
        )
        for label, value, copy_text, copied_text in rows:
            self.put_info(
                label,
                value,
                copy_text=copy_text,
                copied_text=copied_text,
            )
        return True


__all__ = ["GetFileInfo"]
