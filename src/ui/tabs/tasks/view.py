from __future__ import annotations

import tkinter as tk
from tkinter import Canvas, ttk


def build_tasks_tab_shell(window) -> None:
    window.scrollbar = ttk.Scrollbar(window.tab5, orient=tk.VERTICAL)
    window.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    window.canvas1 = Canvas(window.tab5, yscrollcommand=window.scrollbar.set)
    window.canvas1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    window.frame_bg = ttk.Frame(window.canvas1)
    window.canvas1.create_window((0, 0), window=window.frame_bg, anchor='nw')
    window.canvas1.config(highlightthickness=0)


__all__ = ['build_tasks_tab_shell']
