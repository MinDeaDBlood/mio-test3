"""Tk window used by the project ZIP packaging flow."""

from __future__ import annotations

import logging
from tkinter import BOTH, TOP, BooleanVar, IntVar, ttk

from src.ui.common.windowing import Toplevel
from src.ui.localization import LocalizationCatalog
from src.ui.tabs.project.pack import zip_prompt_keys as keys

logger = logging.getLogger(__name__)


def prompt_hybrid_pack_option(
    host_window, *, texts: LocalizationCatalog
) -> bool | None:
    confirm = texts.resolve_required_ui_text(keys.CONFIRM_BUTTON)
    cancel = texts.resolve_required_ui_text(keys.CANCEL_BUTTON)
    dialog = Toplevel(master=host_window)
    dialog.title(
        texts.resolve_required_ui_text(keys.PROJECT_PACK_ZIP_PROMPT_PACK_ZIP)
    )
    value = IntVar(master=dialog, value=0)
    pack_hybrid_rom = BooleanVar(master=dialog, value=False)

    frame_inner = ttk.Frame(dialog)
    frame_inner.pack(expand=True, fill=BOTH, padx=20, pady=20)
    ttk.Label(
        frame_inner,
        text=texts.resolve_required_ui_text(
            keys.PROJECT_PACK_ZIP_PROMPT_REPACK_ZIP_PROMPT
        ),
        font=(None, 15),
        wraplength=400,
    ).pack(side=TOP)
    ttk.Checkbutton(
        frame_inner,
        text=texts.resolve_required_ui_text(
            keys.PROJECT_PACK_ZIP_PROMPT_HYBRID_ZIP_TOOLS_DESCRIPTION
        ),
        variable=pack_hybrid_rom,
        onvalue=True,
        offvalue=False,
    ).pack(side=TOP)

    frame_button = ttk.Frame(frame_inner)

    def close_dialog(selected: int) -> None:
        logger.info(
            "project_zip.options_closed: confirmed=%s hybrid=%s",
            selected == 1,
            pack_hybrid_rom.get(),
        )
        value.set(selected)
        try:
            dialog.grab_release()
        except Exception:
            logger.debug("project_zip.grab_release_skipped", exc_info=True)
        dialog.destroy()

    ttk.Button(
        frame_button,
        text=cancel,
        command=lambda: close_dialog(0),
    ).pack(side="left", padx=5, pady=5, fill=BOTH, expand=True)
    ttk.Button(
        frame_button,
        text=confirm,
        command=lambda: close_dialog(1),
        style="Accent.TButton",
    ).pack(side="left", padx=5, pady=5, fill=BOTH, expand=True)
    frame_button.pack(fill=BOTH)

    dialog.protocol("WM_DELETE_WINDOW", lambda: close_dialog(0))
    dialog.center_on_screen(force=True)
    dialog.grab_set()
    logger.info("project_zip.options_opened")
    dialog.wait_window()
    if value.get() != 1:
        return None
    return bool(pack_hybrid_rom.get())


__all__ = ["prompt_hybrid_pack_option"]
