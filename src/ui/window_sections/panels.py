from __future__ import annotations

import tkinter as tk
from tkinter import Canvas, Label, Text
from tkinter.constants import BOTH, RIGHT, TOP, X
from tkinter import ttk

from src.ui.tabs.registry import main_tab_title
from src.ui.tabs.tasks.view import build_tasks_tab_shell


def build_right_panel(
    window,
    *,
    spec,
    clear_text: str,
    choose_input_file,
    dispatch_input_paths,
    bind_output_streams,
    dnd_files,
):
    window.rzf = ttk.Frame(window.sub_win3)
    window.tsk = Label(window.sub_win3, text=spec.title_text, font=(None, 15))
    window.tsk.pack(padx=10, pady=10, side='top')
    drop_frame = ttk.LabelFrame(window.sub_win3, text=spec.drop_title)
    drop_label = Label(drop_frame, text=spec.drop_hint)
    drop_frame.bind('<Button-1>', lambda *_args: choose_input_file())
    drop_frame.pack(padx=5, pady=5, side='top', fill=X)
    drop_label.bind('<Button-1>', lambda *_args: choose_input_file())
    drop_label.pack(padx=5, pady=5, side='top', fill=X)
    window.scroll = ttk.Scrollbar(window.rzf)
    window.show = Text(window.rzf)
    bind_output_streams(window)
    if spec.stdout_buffer:
        window._stdout_sink.replay(spec.stdout_buffer)
    drop_frame.drop_target_register(dnd_files)
    drop_frame.dnd_bind('<<Drop>>', lambda event: dispatch_input_paths([event.data]))
    drop_label.drop_target_register(dnd_files)
    drop_label.dnd_bind('<<Drop>>', lambda event: dispatch_input_paths([event.data]))
    window.scroll.config(command=window.show.yview)
    window.show.config(yscrollcommand=window.scroll.set)
    window.rzf.pack(padx=5, pady=5, fill=BOTH, side=TOP)
    window.Clear_Load_canvas = Canvas(window.rzf)
    window.Clear_Load_canvas.config(highlightthickness=0)
    ttk.Button(
        window.Clear_Load_canvas,
        text=clear_text,
        command=lambda: window.show.delete(1.0, tk.END),
    ).pack(padx=10, pady=10, side=TOP)
    window.gif_label = Label(window.Clear_Load_canvas)
    window.gif_label.pack(padx=10, pady=10, side=TOP)
    window.Clear_Load_canvas.pack(side=RIGHT, anchor='ne')
    window.scroll.pack(side=RIGHT, fill=BOTH)
    window.show.pack(side=RIGHT, fill=BOTH, expand=True)


def build_notebook_shell(window, *, pro_enabled: bool, texts) -> None:
    window.sub_win2 = ttk.Frame(window)
    window.sub_win3 = ttk.Frame(window)
    window.sub_win2.pack(fill=BOTH, side=RIGHT, expand=True)
    window.sub_win3.pack(fill=BOTH, side=RIGHT, expand=True)
    window.notepad = ttk.Notebook(window.sub_win2)
    if not pro_enabled:
        window.tab = ttk.Frame(window.notepad)
    window.tab2 = ttk.Frame(window.notepad)
    window.tab3 = ttk.Frame(window.notepad)
    window.tab4 = ttk.Frame(window.notepad)
    window.tab5 = ttk.Frame(window.notepad)
    window.tab6 = ttk.Frame(window.notepad)
    window.tab7 = ttk.Frame(window.notepad)
    if not pro_enabled:
        window.notepad.add(window.tab, text=main_tab_title(texts, 'home'))
    window.notepad.add(window.tab2, text=main_tab_title(texts, 'project'))
    window.notepad.add(window.tab7, text=main_tab_title(texts, 'plugins'))
    window.notepad.add(window.tab3, text=main_tab_title(texts, 'settings'))
    window.notepad.add(window.tab4, text=main_tab_title(texts, 'about'))
    window.notepad.add(window.tab5, text=main_tab_title(texts, 'tasks'))
    window.notepad.add(window.tab6, text=main_tab_title(texts, 'tools'))
    build_tasks_tab_shell(window)
    window.notepad.pack(fill=BOTH, expand=True)


__all__ = ['build_notebook_shell', 'build_right_panel']
