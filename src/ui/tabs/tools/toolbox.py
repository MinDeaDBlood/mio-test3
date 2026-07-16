from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from tkinter import Canvas, Frame, ttk
from tkinter.ttk import Scrollbar

from src.ui.tabs.tools import keys


_TOOL_SPECS: tuple[tuple[str, str], ...] = (
    (keys.DOWNLOAD_FIRMWARE_BUTTON, "download_firmware"),
    (keys.GET_FILE_INFO_BUTTON, "get_file_info"),
    (keys.BYTE_CALCULATOR_BUTTON, "byte_calculator"),
    (keys.ALLOW_SELINUX_AUDIT_BUTTON, "allow_selinux_audit"),
    (keys.DISABLE_AVB_BUTTON, "disable_avb"),
    (keys.DISABLE_ENCRYPTION_BUTTON, "disable_encryption"),
    (keys.TRIM_RAW_IMAGE_BUTTON, "trim_raw_image"),
    (keys.MAGISK_PATCH_BUTTON, "magisk_patch"),
    (keys.MERGE_QUALCOMM_IMAGE_BUTTON, "merge_qualcomm_image"),
    (keys.MERGE_SUPER_BUTTON, "merge_super"),
    (keys.SPLIT_SUPER_BUTTON, "split_super"),
    (keys.DECRYPT_XTC_XML_BUTTON, "decrypt_xtc_xml"),
    (keys.MTK_PORT_BUTTON, "mtk_port_tool"),
)


class ToolBox(ttk.Frame):
    """Scrollable collection of tool launch buttons."""

    def __init__(
        self,
        master,
        *,
        openers: Mapping[str, Callable[[], object]],
        texts,
        ensure_texts_loaded: Callable[..., object],
    ) -> None:
        super().__init__(master=master)
        missing = [
            opener_id for _key, opener_id in _TOOL_SPECS if opener_id not in openers
        ]
        if missing:
            raise ValueError(
                f"ToolBox is missing launch callbacks: {', '.join(missing)}"
            )
        self._openers = dict(openers)
        self._texts = texts
        self._ensure_texts_loaded = ensure_texts_loaded
        self.__on_mouse = lambda event: self.canvas.yview_scroll(
            -1 * int(event.delta / 120),
            "units",
        )

    def pack_basic(self):
        scrollbar = Scrollbar(self, orient="vertical")
        scrollbar.pack(side="right", fill="y", padx=10, pady=10)
        self.canvas = Canvas(self, yscrollcommand=scrollbar.set)
        self.canvas.pack_propagate(False)
        self.canvas.pack(fill="both", expand=True)
        scrollbar.config(command=self.canvas.yview)
        self.label_frame = Frame(self.canvas)
        self._canvas_window_id = self.canvas.create_window(
            (0, 0),
            window=self.label_frame,
            anchor="nw",
        )
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", lambda event: self.__on_mouse(event))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(
            self._canvas_window_id, width=max(int(event.width), 1)
        )
        self.update_ui()

    def gui(self):
        required_keys = (keys.TITLE, *(key for key, _opener_id in _TOOL_SPECS))
        self._ensure_texts_loaded(*required_keys)
        self.pack_basic()
        width_controls = 3
        index_row = 0
        index_column = 0
        for column in range(width_controls):
            self.label_frame.grid_columnconfigure(
                column,
                weight=1,
                uniform="toolbox_buttons",
            )

        for key, opener_id in _TOOL_SPECS:
            text = self._texts.resolve_required_ui_text(key)
            if text.startswith("[missing:"):
                logging.warning(
                    "ToolBox localization missing: key=%s; language=%s; language_file=%s; "
                    "caller=src/ui/tabs/tools/toolbox.py:ToolBox.gui",
                    key,
                    self._texts.current_language() or "<unknown>",
                    self._texts.current_language_file() or "<unknown>",
                )
            ttk.Button(
                self.label_frame,
                text=text,
                command=self._openers[opener_id],
                width=17,
            ).grid(
                row=index_row,
                column=index_column,
                padx=5,
                pady=5,
                sticky="ew",
            )
            index_column = (index_column + 1) % width_controls
            if not index_column:
                index_row += 1
        self.update_ui()

    def update_ui(self):
        self.label_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"), highlightthickness=0)


__all__ = ["ToolBox"]
