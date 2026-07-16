from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class IconGrid(tk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.icons = []
        self.apps = {}

        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.canvas.pack(side='left', fill='both', expand=True)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollable_frame_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')

        self.scrollable_frame.bind('<Configure>', self.on_frame_configure)
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        self.canvas.bind('<MouseWheel>', self._on_mousewheel)
        self.canvas.bind('<Button-4>', self._on_mousewheel)
        self.canvas.bind('<Button-5>', self._on_mousewheel)

        self.scrollbar.bind('<MouseWheel>', lambda e: 'break')
        self.scrollbar.bind('<Button-4>', lambda e: 'break')
        self.scrollbar.bind('<Button-5>', lambda e: 'break')

    def _on_mousewheel(self, event):
        if not self.canvas.winfo_exists() or not self.scrollable_frame.winfo_exists() or not self.scrollbar.winfo_exists():
            return
        if hasattr(event, 'widget') and event.widget == self.scrollbar:
            return 'break'
        if self.scrollbar.winfo_ismapped():
            sb_x_abs = self.scrollbar.winfo_rootx()
            sb_y_abs = self.scrollbar.winfo_rooty()
            sb_w = self.scrollbar.winfo_width()
            sb_h = self.scrollbar.winfo_height()
            if sb_x_abs <= event.x_root < sb_x_abs + sb_w and sb_y_abs <= event.y_root < sb_y_abs + sb_h:
                return 'break'
        if self.scrollbar.winfo_ismapped():
            content_h = self.scrollable_frame.winfo_reqheight()
            canvas_h = self.canvas.winfo_height()
            if content_h > canvas_h:
                delta = 0
                if event.num == 4:
                    delta = -1
                elif event.num == 5:
                    delta = 1
                elif hasattr(event, 'delta') and event.delta != 0:
                    delta = int(-1 * (event.delta / 120))
                if delta != 0:
                    self.canvas.yview_scroll(delta, 'units')
                    return 'break'
        return

    def on_canvas_configure(self, event=None):
        if not (self.canvas.winfo_exists() and self.scrollable_frame.winfo_exists() and hasattr(self, 'scrollable_frame_id')):
            return
        canvas_width = self.canvas.winfo_width()
        self.canvas.itemconfig(self.scrollable_frame_id, width=canvas_width)
        if self.scrollable_frame.winfo_exists():
            self.scrollable_frame.configure(width=canvas_width)
            self.scrollable_frame.update_idletasks()
        self.on_frame_configure()

    def on_frame_configure(self, event=None):
        if not (self.canvas.winfo_exists() and self.scrollable_frame.winfo_exists()):
            return
        self.canvas.config(scrollregion=self.canvas.bbox('all'))
        self.scrollable_frame.update_idletasks()
        self.canvas.update_idletasks()
        canvas_height = self.canvas.winfo_height()
        content_height = self.scrollable_frame.winfo_reqheight()
        if content_height > canvas_height + 2:
            if not self.scrollbar.winfo_ismapped():
                self.scrollbar.pack(side='right', fill='y')
        else:
            if self.scrollbar.winfo_ismapped():
                self.scrollbar.pack_forget()

    def add_icon(self, icon_widget, id_, num_columns=4):
        if id_ in self.apps:
            self.remove_icon(id_)
        self.icons.append(icon_widget)
        self.apps[id_] = icon_widget
        row = (len(self.icons) - 1) // num_columns
        col = (len(self.icons) - 1) % num_columns
        icon_widget.grid(in_=self.scrollable_frame, row=row, column=col, padx=10, pady=10, sticky='nsew')
        if self.scrollable_frame.winfo_exists():
            self.scrollable_frame.update_idletasks()
            self.on_frame_configure()

    def remove_icon(self, id_):
        if id_ in self.apps:
            widget_to_remove = self.apps.pop(id_)
            if widget_to_remove in self.icons:
                self.icons.remove(widget_to_remove)
            if widget_to_remove.winfo_exists():
                widget_to_remove.destroy()
            self._rebuild_grid()
            if self.scrollable_frame.winfo_exists():
                self.scrollable_frame.update_idletasks()
                self.on_frame_configure()

    def clean(self):
        ids_to_remove = list(self.apps.keys())
        for id_ in ids_to_remove:
            self.remove_icon(id_)

    def _rebuild_grid(self, num_columns=4):
        if not self.scrollable_frame.winfo_exists():
            return
        for widget in self.scrollable_frame.winfo_children():
            widget.grid_forget()
        for i, widget in enumerate(self.icons):
            if widget.winfo_exists():
                row = i // num_columns
                col = i % num_columns
                widget.grid(in_=self.scrollable_frame, row=row, column=col, padx=10, pady=10, sticky='nsew')
        self.scrollable_frame.update_idletasks()
        self.on_frame_configure()
