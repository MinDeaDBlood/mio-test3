from __future__ import annotations

from tkinter import BOTTOM, HORIZONTAL, LEFT, X, Y, Canvas, Menu, ttk

from src.ui.common.controls import ListBox
from src.ui.tabs.project.unpack.registry import get_option_values
from src.ui.tabs.project.unpack import layout_keys as keys


def build_unpack_view_layout(view) -> None:
    view.pack(padx=5, pady=5)
    view.ch.set(True)
    run_select_canvas = Canvas(view)
    run_select_canvas.config(highlightthickness=0)

    view.fm = ttk.Combobox(
        run_select_canvas, state="readonly", values=get_option_values()
    )
    view.lsg = ListBox(
        view,
        texts=view.texts,
        set_all_text=view.texts.resolve_required_ui_text(keys.SELECT_ALL_CHECKBOX),
    )
    view.menu = Menu(view.lsg, tearoff=False, borderwidth=0)
    view.menu.add_command(
        label=view.texts.resolve_required_ui_text(keys.IMAGE_INFO_MENU_ACTION),
        command=view.info,
    )
    view.lsg.bind("<Button-3>", view.show_menu)

    view.fm.current(0)
    view.fm.bind("<<ComboboxSelected>>", lambda *x: view.refs())
    view.lsg.gui()
    view.lsg.canvas.bind("<Button-3>", view.show_menu)

    mode_frame = ttk.Frame(view)
    ttk.Radiobutton(
        mode_frame,
        text=view.texts.resolve_required_ui_text(keys.UNPACK_MODE_OPTION),
        variable=view.ch,
        value=True,
    ).pack(padx=5, pady=5, side="left")
    ttk.Radiobutton(
        mode_frame,
        text=view.texts.resolve_required_ui_text(keys.PACK_MODE_OPTION),
        variable=view.ch,
        value=False,
    ).pack(padx=5, pady=5, side="left")

    view.fm.pack(padx=5, pady=5, fill=Y, side=LEFT)
    ttk.Button(
        run_select_canvas,
        text=view.texts.resolve_required_ui_text(keys.RUN_BUTTON),
        command=view.start_action,
    ).pack(padx=5, pady=5, side=LEFT)

    run_select_canvas.pack(side=BOTTOM, fill=X)
    ttk.Separator(view, orient=HORIZONTAL).pack(padx=50, side=BOTTOM, fill=X)
    mode_frame.pack(padx=5, pady=5, fill=X, side=BOTTOM)
    ttk.Separator(view, orient=HORIZONTAL).pack(padx=50, side=BOTTOM, fill=X)
    view.lsg.pack(padx=5, pady=5, fill=Y, side=BOTTOM, expand=True)
    view.ch.trace("w", lambda *x: view.hd())


__all__ = ["build_unpack_view_layout"]
