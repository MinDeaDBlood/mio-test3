import logging
import os
import tkinter as tk
from tkinter import ttk

from src.ui.common.dnd import Tk as _MainWindowBase
from src.ui.common.window_appearance import register_window
from src.ui import main_window_keys as keys
from src.ui.warn.dialogs import warn_win
from src.ui.window_sections.main_window_presenter import (
    apply_windows_alpha_fix,
    apply_windows_font_fix,
    current_clock_text,
    safe_initial_alpha,
)


class Tool(_MainWindowBase):
    def __init__(self, *, texts, tkdnd_library_root):
        from PIL.ImageTk import PhotoImage

        from src.ui.assets import images
        from src.ui.common.themes.sv_ttk_fixes import do_set_window_deffont

        super().__init__(tkdnd_library_root=tkdnd_library_root)
        register_window(self)
        self._texts = texts
        self.rotate_angle = 0
        self.loops = []
        initial_alpha = safe_initial_alpha(self, logger=logging)
        apply_windows_font_fix(
            self, logger=logging, do_set_window_deffont=do_set_window_deffont
        )
        self.title(self._texts.resolve_required_ui_text(keys.WINDOW_TITLE))
        if os.name != "posix" and hasattr(images, "icon_byte"):
            try:
                self.iconphoto(True, PhotoImage(data=images.icon_byte))
            except Exception as exc:
                logging.error("Failed to set application icon: %s", exc)
        apply_windows_alpha_fix(self, initial_alpha=initial_alpha, logger=logging)

    def message_pop(
        self,
        text: str = "",
        color: str = "red",
        title: str | None = None,
        master: object | None = None,
    ) -> None:
        warn_win(
            texts=self._texts,
            text=text,
            color=color,
            title=title,
            master=master if isinstance(master, tk.Toplevel) else None,
        )

    def get_time(self):
        self.tsk.config(text=current_clock_text())
        self.after(1000, self.get_time)

    def get_frame(self, title):
        frame = ttk.LabelFrame(self.frame_bg, text=title)
        frame.pack(padx=10, pady=10)
        ttk.Button(
            frame, text=self._texts.resolve_required_ui_text(keys.MAIN_WINDOW_CLOSE), command=frame.destroy
        ).pack(anchor="ne", padx=5, pady=5)
        self.update_frame()
        self.scrollbar.config(command=self.canvas1.yview)
        return frame

    def update_frame(self):
        self.frame_bg.update_idletasks()
        self.canvas1.config(scrollregion=self.canvas1.bbox("all"))

    def start_loops(self):
        for callback in self.loops:
            callback()
