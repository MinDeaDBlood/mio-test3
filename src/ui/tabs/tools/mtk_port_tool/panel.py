from __future__ import annotations

from tkinter import BooleanVar, Canvas, StringVar, ttk
from tkinter.filedialog import askopenfilename

from src.ui.common.windowing import Toplevel
from src.ui.contracts import (
    MtkPortControllerPort,
    MtkPortProfileProtocol,
    MtkPortResultProtocol,
)
from src.ui.localization import LocalizationCatalog
from src.ui.tabs.tools.mtk_port_tool import keys
from src.ui.warn.dialogs import info_win, warn_win


class FileChooser(Toplevel):
    """Dialog that collects the three source files required by the MTK tool."""

    def __init__(
        self,
        parent,
        *,
        texts: LocalizationCatalog,
        initial_directory: str,
        default_boot_image: str = "",
        default_system_image: str = "",
    ):
        super().__init__(parent)
        self._texts = texts
        self.title(self._text(keys.FILE_DIALOG_TITLE))
        self._initial_directory = initial_directory
        self._default_boot_image = default_boot_image
        self._default_system_image = default_system_image
        self.portzip = StringVar()
        self.basesys = StringVar(value=default_system_image)
        self.baseboot = StringVar(value=default_boot_image)

        self._setup_widgets()
        self.focus()

    def _text(self, key: str) -> str:
        return self._texts.resolve_required_ui_text(key)

    def _choose_file(self, target: StringVar, *, title: str) -> None:
        selected = askopenfilename(
            initialdir=self._initial_directory,
            title=title,
        )
        if selected:
            target.set(selected)
        self.focus()

    def _setup_widgets(self) -> None:
        rows = (
            (
                self._text(keys.PORT_ROM_LABEL),
                self.portzip,
                self._text(keys.PORT_ROM_BROWSE_BUTTON),
                self._text(keys.PORT_ROM_SELECT_TITLE),
            ),
            (
                self._text(keys.BOOT_IMAGE_LABEL),
                self.baseboot,
                self._text(keys.BOOT_IMAGE_BROWSE_BUTTON),
                self._text(keys.BOOT_IMAGE_SELECT_TITLE),
            ),
            (
                self._text(keys.SYSTEM_IMAGE_LABEL),
                self.basesys,
                self._text(keys.SYSTEM_IMAGE_BROWSE_BUTTON),
                self._text(keys.SYSTEM_IMAGE_SELECT_TITLE),
            ),
        )
        for label_text, value, browse_text, select_title in rows:
            frame = ttk.Frame(self)
            frame.pack(side="top", fill="x", padx=5, pady=5)
            ttk.Label(frame, text=label_text, width=16).pack(
                side="left",
                padx=5,
                pady=5,
            )
            ttk.Entry(frame, textvariable=value, width=40).pack(
                side="left",
                fill="x",
                padx=5,
                pady=5,
                expand=True,
            )
            ttk.Button(
                frame,
                text=browse_text,
                command=lambda current=value,
                current_title=select_title: self._choose_file(
                    current,
                    title=current_title,
                ),
            ).pack(side="left", padx=5, pady=5)
        bottom_frame = ttk.Frame(self)
        ttk.Button(
            bottom_frame,
            text=self._text(keys.FILE_DIALOG_OK_BUTTON),
            command=self.destroy,
        ).pack(side="right", padx=5, pady=5)
        bottom_frame.pack(side="bottom", fill="x", padx=5, pady=5)

    def get(self) -> tuple[str, str, str]:
        self.wait_window(self)
        return self.baseboot.get(), self.basesys.get(), self.portzip.get()


class MtkPortPanel(ttk.Labelframe):
    """Presentation-only panel for configuring and starting the MTK workflow."""

    def __init__(
        self,
        parent,
        *,
        texts: LocalizationCatalog,
        controller: MtkPortControllerPort,
        initial_directory: str,
        default_boot_image: str = "",
        default_system_image: str = "",
    ):
        self._texts = texts
        super().__init__(parent, text=self._text(keys.TOOL_GROUP_TITLE))
        self._controller = controller
        self._initial_directory = initial_directory
        self._default_boot_image = default_boot_image
        self._default_system_image = default_system_image
        self._profiles = {profile.name: profile for profile in controller.profiles()}
        if not self._profiles:
            raise RuntimeError(self._text(keys.PROFILES_MISSING_ERROR))

        first_profile = next(iter(self._profiles))
        self.chipset_select = StringVar(value=first_profile)
        self.pack_type = StringVar(value="zip")
        self.patch_magisk = BooleanVar(value=False)
        self.target_arch = StringVar(value="arm64-v8a")
        self.magisk_apk = StringVar(value="magisk.apk")
        self._flag_vars: dict[str, BooleanVar] = {}
        self._flag_widgets: list[ttk.Checkbutton] = []
        self._setup_widgets()

    def _text(self, key: str) -> str:
        return self._texts.resolve_required_ui_text(key)

    def _warn(self, message: str) -> None:
        warn_win(
            texts=self._texts,
            text=message,
            title=self._text(keys.WARNING_DIALOG_TITLE),
            ok=self._text(keys.WARNING_DIALOG_OK_BUTTON),
        )

    def _inform(self, message: str) -> None:
        info_win(
            message,
            texts=self._texts,
            title=self._text(keys.INFORMATION_DIALOG_TITLE),
            ok=self._text(keys.INFORMATION_DIALOG_OK_BUTTON),
        )

    def _start_port(self) -> None:
        if not self._flag_vars:
            self._warn(self._text(keys.NO_ACTIONS_MESSAGE))
            return
        boot, system, port_rom = FileChooser(
            self,
            texts=self._texts,
            initial_directory=self._initial_directory,
            default_boot_image=self._default_boot_image,
            default_system_image=self._default_system_image,
        ).get()
        magisk_path = self.magisk_apk.get() if self.patch_magisk.get() else None
        self._set_running(True)
        self._controller.start(
            profile_name=self.chipset_select.get(),
            boot_image=boot,
            system_image=system,
            port_rom=port_rom,
            enabled_flags={
                name: value.get() for name, value in self._flag_vars.items()
            },
            output_as_image=self.pack_type.get() == "img",
            patch_magisk=self.patch_magisk.get(),
            magisk_apk=magisk_path,
            target_arch=self.target_arch.get(),
            on_success=self._show_success,
            on_error=self._show_error,
            on_finally=lambda: self._set_running(False),
        )

    def _show_success(self, result: MtkPortResultProtocol) -> None:
        self._inform(
            self._text(keys.COMPLETE_MESSAGE).format(path=result.output_directory)
        )

    def _show_error(self, exc: Exception) -> None:
        self._warn(str(exc))

    def _set_running(self, running: bool) -> None:
        self._port_button.config(state="disabled" if running else "normal")

    def _load_profile_flags(self, profile_name: str) -> None:
        profile: MtkPortProfileProtocol = self._profiles[profile_name]
        self._flag_vars.clear()
        for widget in self._flag_widgets:
            widget.destroy()
        self._flag_widgets.clear()
        for name, enabled in profile.flags.items():
            variable = BooleanVar(value=enabled)
            self._flag_vars[name] = variable
            widget = ttk.Checkbutton(self._flags_frame, text=name, variable=variable)
            widget.pack(side="top", fill="x", padx=5)
            self._flag_widgets.append(widget)
        self._flags_canvas.configure(scrollregion=self._flags_canvas.bbox("all"))

    def _choose_magisk_apk(self, _event=None) -> None:
        selected = askopenfilename(
            initialdir=self._initial_directory,
            title=self._text(keys.MAGISK_APK_SELECT_TITLE),
        )
        if selected:
            self.magisk_apk.set(selected)

    def _toggle_magisk_fields(self) -> None:
        if self.patch_magisk.get():
            self._magisk_arch.grid(
                column=0,
                row=2,
                padx=5,
                pady=5,
                sticky="nsew",
                columnspan=2,
            )
            self._magisk_entry.grid(
                column=0,
                row=3,
                padx=5,
                pady=5,
                sticky="nsew",
                columnspan=2,
            )
        else:
            self._magisk_entry.grid_forget()
            self._magisk_arch.grid_forget()

    def _setup_widgets(self) -> None:
        options = ttk.Frame(self)
        selector = ttk.Frame(options)
        ttk.Label(
            selector,
            text=self._text(keys.SOC_TYPE_LABEL),
            anchor="e",
        ).pack(side="left", padx=5, pady=5)
        ttk.OptionMenu(
            selector,
            self.chipset_select,
            self.chipset_select.get(),
            *self._profiles,
            command=self._load_profile_flags,
        ).pack(side="left", fill="x", padx=5, pady=5)
        selector.pack(side="top", fill="x")

        actions = ttk.Labelframe(
            options,
            text=self._text(keys.SUPPORTED_ACTIONS_GROUP_TITLE),
            height=180,
        )
        self._flags_canvas = Canvas(actions)
        scrollbar = ttk.Scrollbar(
            actions,
            orient="vertical",
            command=self._flags_canvas.yview,
        )
        self._flags_canvas.configure(
            yscrollcommand=scrollbar.set,
            yscrollincrement=1,
        )
        self._flags_frame = ttk.Frame(self._flags_canvas)
        self._flags_canvas.create_window(0, 0, window=self._flags_frame, anchor="nw")
        self._flags_frame.bind(
            "<Configure>",
            lambda _event: self._flags_canvas.configure(
                scrollregion=self._flags_canvas.bbox("all"),
                width=300,
                height=180,
            ),
        )
        self._flags_canvas.bind(
            "<MouseWheel>",
            lambda event: self._flags_canvas.yview_scroll(
                int(-event.delta / 2),
                "units",
            ),
        )
        scrollbar.pack(side="right", fill="y")
        self._flags_canvas.pack(side="right", fill="x", expand=True, anchor="e")
        actions.pack(side="top", fill="x", expand=True)

        controls = ttk.Frame(options)
        self._port_button = ttk.Button(
            options,
            text=self._text(keys.PORT_BUTTON),
            command=self._start_port,
        )
        self._port_button.pack(
            side="top",
            fill="both",
            padx=5,
            pady=5,
            expand=True,
        )
        ttk.Radiobutton(
            controls,
            text=self._text(keys.OUTPUT_ZIP_RADIO),
            variable=self.pack_type,
            value="zip",
        ).grid(column=0, row=0, padx=5, pady=5)
        ttk.Radiobutton(
            controls,
            text=self._text(keys.OUTPUT_IMAGE_RADIO),
            variable=self.pack_type,
            value="img",
        ).grid(column=1, row=0, padx=5, pady=5)
        self._magisk_arch = ttk.OptionMenu(
            controls,
            self.target_arch,
            self.target_arch.get(),
            "arm64-v8a",
            "armeabi-v7a",
            "x86",
            "x86_64",
        )
        self._magisk_entry = ttk.Entry(controls, textvariable=self.magisk_apk)
        self._magisk_entry.bind("<Button-1>", self._choose_magisk_apk)
        ttk.Checkbutton(
            controls,
            text=self._text(keys.PATCH_MAGISK_CHECKBOX),
            variable=self.patch_magisk,
            command=self._toggle_magisk_fields,
        ).grid(column=0, row=1, padx=5, pady=5, sticky="w")
        controls.pack(side="top", padx=5, pady=5, fill="x", expand=True)
        options.pack(side="left", padx=5, pady=5, fill="y")
        self._load_profile_flags(self.chipset_select.get())


__all__ = ["FileChooser", "MtkPortPanel"]
