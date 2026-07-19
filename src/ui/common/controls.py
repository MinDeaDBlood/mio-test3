# Copyright (C) 2022-2025 The MIO-KITCHEN-SOURCE Project
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.gnu.org/licenses/agpl-3.0.en.html#license-text
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import tkinter
from tkinter import (
    Canvas,
    X,
    BooleanVar,
    HORIZONTAL,
    TclError,
    Tk,
    StringVar,
    ttk,
    BOTH,
)
from tkinter.ttk import Frame, Scrollbar, Checkbutton, Separator

from src.ui.localization import LocalizationCatalog
from src.ui.common.windowing import Toplevel
from src.ui.common import controls_keys as keys


def input_(
    *,
    texts: LocalizationCatalog,
    title: str | None = None,
    text: str = "",
    master: Tk | Toplevel | tkinter.Frame | None = None,
) -> str:
    owns_window = master is None
    if master is None:
        master = Toplevel()
    if not title:
        title = texts.resolve_required_ui_text(keys.INPUT_DIALOG_DEFAULT_TITLE)
    input_var = StringVar(master=master, value=text)
    input_frame = ttk.LabelFrame(master, text=title)
    input_frame.place(relx=0.5, rely=0.5, anchor="center")
    entry = ttk.Entry(input_frame, textvariable=input_var)
    entry.pack(pady=5, padx=5, fill=BOTH)
    entry.focus_set()
    entry.bind("<Return>", lambda *x: input_frame.destroy())
    ttk.Button(
        input_frame,
        text=texts.resolve_required_ui_text(keys.INPUT_DIALOG_OK_BUTTON),
        command=input_frame.destroy,
    ).pack(padx=5, pady=5, fill=BOTH, side="bottom")
    input_frame.wait_window()
    value = input_var.get()
    if owns_window and master.winfo_exists():
        master.destroy()
    return value


class ListBox(Frame):
    def __init__(
        self,
        master,
        *,
        texts: LocalizationCatalog,
        set_all_text: str | None = None,
    ):
        super().__init__(master=master)
        self._texts = texts
        self._set_all_text = set_all_text
        self.var = None
        self.set_all = None
        self.label_frame = None
        self.canvas = None
        self.selected: list = []
        self.vars = []
        self.controls = []
        self.loaded_value = []

    def __on_mouse(self, event):
        self.canvas.yview_scroll(-1 * (int(event.delta / 120)), "units")

    def clear(self):
        self.selected.clear()
        for i in self.controls:
            try:
                i.destroy()
            except (TclError, AttributeError, ValueError):
                pass
        self.controls.clear()
        self.vars.clear()
        self.loaded_value.clear()
        self.var.set(False)

    def gui(self):
        self.var = BooleanVar(value=False)
        scrollbar = Scrollbar(self, orient="vertical")
        self.canvas = Canvas(self, yscrollcommand=scrollbar.set, width=250, height=150)
        self.canvas.pack_propagate(False)
        scrollbar.config(command=self.canvas.yview)
        self.label_frame = Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.label_frame, anchor="nw")
        self.canvas.bind("<MouseWheel>", lambda event: self.__on_mouse(event))
        self.set_all = Checkbutton(
            self,
            text=self._set_all_text
            or self._texts.resolve_required_ui_text(keys.LISTBOX_SELECT_ALL_CHECKBOX),
            variable=self.var,
            onvalue=True,
            offvalue=False,
            command=lambda *x, var_=self.var: [i.set(True) for i in self.vars]
            if var_.get()
            else [i.set(False) for i in self.vars],
        )

        self.set_all.pack(padx=5, pady=5, anchor="sw", side="bottom")
        Separator(self, orient=HORIZONTAL).pack(padx=10, pady=10, fill=X, side="bottom")
        scrollbar.pack(side="right", fill="y", padx=10, pady=10)
        self.canvas.pack(fill="both", expand=True)

        self.update_ui()

    def update_ui(self):
        self.label_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"), highlightthickness=0)

    def __set_value(self, var, value):
        if var.get():
            if value not in self.selected:
                self.selected.append(value)
        else:
            if value in self.selected:
                self.selected.remove(value)
        self.var.set(True if all(i.get() for i in self.vars) else False)

    def insert(
        self,
        text: str = "",
        value: str = "",
        state=False,
        *,
        refresh: bool = True,
    ):
        if value in self.loaded_value:
            return
        self.loaded_value.append(value)
        var = BooleanVar(value=state)
        c = Checkbutton(
            self.label_frame, text=text, variable=var, onvalue=True, offvalue=False
        )
        self.vars.append(var)
        args = (var, value)
        var.trace_add("write", lambda *x, arg=args: self.__set_value(*arg))
        if state:
            self.__set_value(var, value)
        self.controls.append(c)
        c.pack(anchor="nw", fill="y", padx=5, pady=3)
        if refresh:
            self.update_ui()


class ScrollFrame(Frame):
    def __init__(self, master):
        super().__init__(master=master)
        self.var = None
        self.set_all = None
        self.label_frame = None
        self.canvas = None
        self.controls = []
        self.__on_mouse = lambda event: self.canvas.yview_scroll(
            -1 * (int(event.delta / 120)), "units"
        )

    def clear(self):
        for i in self.controls:
            try:
                i.destroy()
            except (TclError, AttributeError, ValueError):
                pass

    def gui(self):
        scrollbar = Scrollbar(self, orient="vertical")
        scrollbar.pack(side="right", fill="y", padx=10)
        self.canvas = Canvas(self, yscrollcommand=scrollbar.set, height=450)
        self.canvas.pack(fill="both", expand=True)
        scrollbar.config(command=self.canvas.yview)
        self.label_frame = Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.label_frame, anchor="nw")
        self.canvas.bind("<MouseWheel>", lambda event: self.__on_mouse(event))
        self.bind("<MouseWheel>", lambda event: self.__on_mouse(event))
        self.label_frame.bind("<MouseWheel>", lambda event: self.__on_mouse(event))
        self.update_ui()

    def update_ui(self):
        self.label_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"), highlightthickness=0)


class ToggledFrame(Frame):
    def __init__(
        self,
        master,
        text="",
        font=(None, None),
        callback=None,
        unfold: bool = False,
        *args,
        **options,
    ):
        super().__init__(master=master, *args, **options)
        self.callback = callback
        self.show = BooleanVar(value=False)

        self.title_frame = ttk.Frame(self)
        self.title_frame.pack(fill="x", expand=1, padx=10, pady=5)

        self.title_label = ttk.Label(self.title_frame, text=text)
        self.title_label.pack(side="left", fill="x", expand=1, padx=10, pady=5)
        if all(font):
            self.title_label.config(font=font)

        self.toggle_button = ttk.Checkbutton(
            self.title_frame,
            width=1,
            onvalue=True,
            offvalue=False,
            command=self.toggle,
            variable=self.show,
            style="TMenubutton",
        )
        self.toggle_button.pack(side="right")

        self.sub_frame = Frame(self)
        self.sub_frame.config(borderwidth=1)
        if unfold:
            self.show.set(unfold)
            self.toggle()

    def toggle(self):
        if self.show.get():
            self.sub_frame.pack(fill="x", expand=1)
        else:
            self.sub_frame.forget()
        if callable(self.callback):
            self.callback()
