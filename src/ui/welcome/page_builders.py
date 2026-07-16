from __future__ import annotations

import tkinter as tk
from tkinter import BOTH, LEFT, X, HORIZONTAL, ttk

from src.ui.welcome import page_builders_keys as keys
from src.ui.welcome.contracts import WelcomeViewPort
from src.ui.welcome.styles import CONTENT_PAD_X, CONTENT_PAD_Y, SECTION_GAP, TEXT_INSET


def _title(view: WelcomeViewPort, text: str, *, hero: bool = False) -> ttk.Label:
    return ttk.Label(
        view.frame,
        text=text,
        font=view.fonts.hero if hero else view.fonts.title,
        anchor="w",
        justify="left",
        wraplength=view.content_wrap_width,
    )


def _body(view: WelcomeViewPort, text: str) -> ttk.Label:
    return ttk.Label(
        view.frame,
        text=text,
        font=view.fonts.body,
        anchor="w",
        justify="left",
        wraplength=view.content_wrap_width,
    )


def _note(view: WelcomeViewPort, text: str) -> ttk.Label:
    return ttk.Label(
        view.frame,
        text=text,
        font=view.fonts.note,
        anchor="w",
        justify="left",
        wraplength=view.content_wrap_width,
    )


def _pack_title(view: WelcomeViewPort, text: str, *, hero: bool = False) -> None:
    _title(view, text, hero=hero).pack(
        padx=CONTENT_PAD_X,
        pady=(CONTENT_PAD_Y, SECTION_GAP),
        fill=X,
        anchor="w",
    )
    ttk.Separator(view.frame, orient=HORIZONTAL).pack(
        padx=CONTENT_PAD_X,
        pady=(0, SECTION_GAP),
        fill=X,
    )


def _replace_read_only_text(widget: tk.Text, text: str) -> None:
    widget.config(state="normal")
    widget.delete("1.0", tk.END)
    widget.insert("1.0", text)
    widget.config(state="disabled")
    widget.yview_moveto(0.0)


def _create_read_only_text(
    parent: ttk.Frame, *, height: int = 11
) -> tuple[ttk.Frame, tk.Text]:
    container = ttk.Frame(parent)
    scrollbar = ttk.Scrollbar(container, orient="vertical")
    text_widget = tk.Text(
        container,
        height=height,
        wrap="word",
        padx=TEXT_INSET,
        pady=TEXT_INSET,
        undo=False,
    )
    text_widget.pack(fill=BOTH, side=LEFT, expand=True)
    scrollbar.config(command=text_widget.yview)
    scrollbar.pack(fill="y", side="right")
    text_widget.config(yscrollcommand=scrollbar.set, state="disabled")
    return container, text_widget


def build_hello(view: WelcomeViewPort) -> None:
    _pack_title(view, view.texts.resolve_required_ui_text(keys.WELCOME_TITLE), hero=True)
    _body(view, view.texts.resolve_required_ui_text(keys.WELCOME_GET_STARTED)).pack(
        padx=CONTENT_PAD_X,
        pady=CONTENT_PAD_Y,
        fill=BOTH,
        expand=True,
        anchor="w",
    )


def build_main(view: WelcomeViewPort) -> None:
    data = view.controller.main_data()
    if not view.language_var.get().strip():
        view.language_var.set(data.selected_language)
    _pack_title(view, view.texts.resolve_required_ui_text(keys.LANGUAGE_SELECT_LABEL))
    combobox = ttk.Combobox(
        view.frame,
        state="readonly",
        textvariable=view.language_var,
        values=data.languages,
        width=32,
    )
    combobox.pack(padx=CONTENT_PAD_X, pady=CONTENT_PAD_Y, side="top", fill=X)
    combobox.bind(
        "<<ComboboxSelected>>",
        lambda *_: view.actions.apply_language(view.language_var.get()),
    )


def build_set_workdir(view: WelcomeViewPort) -> None:
    data = view.controller.workdir_data()
    displayed_path = tk.StringVar(master=view.frame, value=data.workdir)

    def choose_workdir() -> None:
        folder = view.actions.choose_workdir()
        if folder:
            displayed_path.set(view.controller.set_workdir(folder))

    _pack_title(view, view.texts.resolve_required_ui_text(keys.WORKING_DIRECTORY_LABEL))
    row = ttk.Frame(view.frame)
    row.pack(fill=X, padx=CONTENT_PAD_X, pady=CONTENT_PAD_Y)
    row.columnconfigure(0, weight=1)
    path_label = ttk.Label(
        row,
        textvariable=displayed_path,
        wraplength=max(view.content_wrap_width - 170, 220),
        anchor="w",
        justify="left",
        cursor="hand2",
    )
    path_label.bind(
        "<Button-1>", lambda *_: view.actions.open_workdir(displayed_path.get())
    )
    path_label.grid(row=0, column=0, sticky="ew", padx=(0, SECTION_GAP))
    ttk.Button(
        row,
        text=view.texts.resolve_required_ui_text(keys.CHANGE_WORKING_DIRECTORY_BUTTON),
        command=choose_workdir,
        width=14,
    ).grid(
        row=0,
        column=1,
        sticky="e",
    )


def build_license(view: WelcomeViewPort) -> None:
    data = view.controller.license_data()
    selected_license = tk.StringVar(master=view.frame, value=data.selected_license)
    _pack_title(view, view.texts.resolve_required_ui_text(keys.OPEN_SOURCE_LICENSE_TITLE))

    combobox = ttk.Combobox(
        view.frame,
        state="readonly",
        textvariable=selected_license,
        values=data.licenses,
    )
    combobox.pack(padx=CONTENT_PAD_X, pady=(0, SECTION_GAP), side="top", fill=X)

    text_container, text_widget = _create_read_only_text(view.frame)
    text_container.pack(fill=BOTH, side="top", expand=True, padx=CONTENT_PAD_X)

    def load_license() -> None:
        _replace_read_only_text(
            text_widget, view.controller.read_license(selected_license.get())
        )

    combobox.bind("<<ComboboxSelected>>", lambda *_: load_license())
    if data.licenses:
        combobox.current(0)
    _replace_read_only_text(text_widget, data.license_text)
    _note(view, view.texts.resolve_required_ui_text(keys.AGREEMENT_NOTICE)).pack(
        fill=X, padx=CONTENT_PAD_X, pady=(SECTION_GAP, 0)
    )


def build_private(view: WelcomeViewPort) -> None:
    _pack_title(view, view.texts.resolve_required_ui_text(keys.AGREEMENT_TITLE))
    text_container, text_widget = _create_read_only_text(view.frame)
    text_container.pack(fill=BOTH, expand=True, padx=CONTENT_PAD_X)
    _replace_read_only_text(text_widget, view.controller.read_private_notice())
    _note(view, view.texts.resolve_required_ui_text(keys.AGREEMENT_CONFIRMATION)).pack(
        fill=X, padx=CONTENT_PAD_X, pady=(SECTION_GAP, 0)
    )


def build_done(view: WelcomeViewPort) -> None:
    _pack_title(view, view.texts.resolve_required_ui_text(keys.COMPLETE_TITLE))
    _body(view, view.texts.resolve_required_ui_text(keys.COMPLETE_MESSAGE)).pack(
        side="top",
        fill=BOTH,
        padx=CONTENT_PAD_X,
        pady=CONTENT_PAD_Y,
        expand=True,
        anchor="w",
    )


__all__ = [
    "build_done",
    "build_hello",
    "build_license",
    "build_main",
    "build_private",
    "build_set_workdir",
]
