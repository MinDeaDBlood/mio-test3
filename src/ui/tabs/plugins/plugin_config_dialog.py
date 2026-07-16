from __future__ import annotations

from collections.abc import Callable
from inspect import signature

import tkinter as tk
from tkinter import BOTH, LEFT, Frame, IntVar, StringVar, X
from tkinter import ttk

from src.ui.common.windowing import Toplevel
from src.ui.localization import LocalizationCatalog
from src.ui.tabs.plugins import module_dialogs_keys as keys


class PluginConfigDialog(Toplevel):
    def _text(self, master, text, fontsize, side):
        ttk.Label(master, text=text, font=(None, int(fontsize))).pack(
            side=side, padx=5, pady=5
        )

    def _button(self, master, text, command):
        ttk.Button(
            master,
            text=text,
            command=lambda: self.config_service.execute_command(
                command, {"dialog": self}
            ),
        ).pack(side="left")

    def _filechose(self, master, set, text):
        frame = ttk.Frame(master)
        frame.pack(fill=X)
        self.values[set] = StringVar()
        ttk.Label(frame, text=text).pack(side="left", padx=10, pady=10)
        ttk.Entry(frame, textvariable=self.values[set]).pack(
            side="left", padx=5, pady=5
        )
        ttk.Button(
            frame,
            text=self._texts.resolve_required_ui_text(keys.PLUGINS_MODULE_DIALOGS_BROWSE),
            command=lambda: self.values[set].set(self.choose_file()),
        ).pack(side="left", padx=10, pady=10)

    def _radio(self, master, set, opins, side):
        self.values[set] = StringVar()
        frame = ttk.Frame(master)
        frame.pack(padx=10, pady=10)
        for option in opins.split():
            text, value = option.split("|")
            self.values[set].set(value)
            ttk.Radiobutton(
                frame, text=text, variable=self.values[set], value=value
            ).pack(side=side)

    def _input(self, master, set, text):
        frame = Frame(master)
        frame.pack(fill=X, padx=5, pady=5)
        self.values[set] = StringVar()
        if text != "None":
            ttk.Label(frame, text=text).pack(side=LEFT, padx=5, pady=5, fill=X)
        ttk.Entry(frame, textvariable=self.values[set]).pack(
            side=LEFT, pady=5, padx=5, fill=X
        )

    def _checkbutton(self, master, set, text):
        self.values[set] = IntVar()
        text = "" if text == "None" else text
        ttk.Checkbutton(
            master,
            text=text,
            variable=self.values[set],
            onvalue=1,
            offvalue=0,
            style="Switch.TCheckbutton",
        ).pack(padx=5, pady=5, fill=BOTH)

    def __unknown(self, master, type, side):
        self.cancelled = self.assert_unknown_control
        self._text(
            master,
            self._texts.resolve_required_ui_text(
                keys.CONFIG_DIALOG_UNKNOWN_WIDGET_FORMAT
            ).format(type),
            10,
            side if side != "None" else "bottom",
        )

    def _cancel(self):
        self.cancelled = True
        self.destroy()

    def __init__(
        self,
        jsons,
        *,
        texts: LocalizationCatalog,
        config_service,
        choose_file: Callable[[], str],
        show_error: Callable[[str], object],
    ):
        super().__init__()
        self._texts = texts
        self.config_service = config_service
        self.choose_file = choose_file
        self.values: dict[str, tk.Variable] = {}
        self.cancelled = False
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        try:
            data = self.config_service.load(jsons)
        except Exception as exc:
            show_error(
                self._texts.resolve_required_ui_text(keys.PLUGINS_MODULE_DIALOGS_PLUGIN_PARSE_FAILED) + str(exc)
            )
            self.cancelled = True
            self.destroy()
            return
        self.title(data.info.title)
        self.assert_unknown_control = data.info.assert_unknown_control
        if data.info.height.lower() != "none" and data.info.width.lower() != "none":
            self.geometry(f"{data.info.width}x{data.info.height}")
        self.attributes("-topmost", "true")
        self.resizable(data.info.resize, data.info.resize)
        control_factories = {
            "text": self._text,
            "button": self._button,
            "filechose": self._filechose,
            "radio": self._radio,
            "input": self._input,
            "checkbutton": self._checkbutton,
        }
        for group in data.groups:
            group_frame = ttk.LabelFrame(self, text=group.title)
            group_frame.pack(padx=10, pady=10)
            for control_data in group.controls:
                control = control_factories.get(
                    control_data.control_type, self.__unknown
                )
                parameter_names = tuple(signature(control).parameters)
                args = [group_frame]
                args.extend(
                    control_data.value_for(name)
                    for name in parameter_names
                    if name != "master"
                )
                control(*args)
        ttk.Button(
            self,
            text=self._texts.resolve_required_ui_text(keys.CONFIG_DIALOG_OK_BUTTON),
            command=self.destroy,
        ).pack(fill=X, side="bottom")
        self.center_on_screen(force=True)
        self.wait_window()


__all__ = ["PluginConfigDialog"]
