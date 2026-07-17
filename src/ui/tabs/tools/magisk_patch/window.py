from __future__ import annotations

import logging
from collections.abc import Callable
from tkinter import BooleanVar, LEFT, StringVar, X, ttk

from src.ui.common.windowing import Toplevel
from src.ui.common.technical_choices import build_choice_set
from src.ui.contracts import MagiskPatchControllerPort
from src.ui.tabs.tools.magisk_patch import keys
from src.ui.warn.dialogs import info_win, warn_win


_SUPPORTED_ARCHITECTURES = ("arm64-v8a", "armeabi-v7a", "x86", "x86_64")


class MagiskPatcher(Toplevel):
    def __init__(self, *, language, choose_file: Callable[..., str]) -> None:
        super().__init__()
        self._language = language
        self._choose_file = choose_file
        self._controller: MagiskPatchControllerPort | None = None
        self.magisk_apk = StringVar()
        self.boot_file = StringVar()
        self._arch_choices = build_choice_set(
            self._language, _SUPPORTED_ARCHITECTURES
        )
        self.magisk_arch = StringVar(
            value=self._arch_choices.label_for("arm64-v8a")
        )
        self.title(self._text(keys.TITLE))
        self._build_ui()
        self.center_on_screen(force=True)

    def _text(self, key: str) -> str:
        return self._language.resolve_required_ui_text(key)

    def _warn(self, message: str) -> None:
        warn_win(
            texts=self._language,
            text=message,
            title=self._text(keys.WARNING_DIALOG_TITLE),
            ok=self._text(keys.WARNING_DIALOG_OK_BUTTON),
        )

    def _inform(self, message: str) -> None:
        info_win(
            message,
            texts=self._language,
            title=self._text(keys.SUCCESS_DIALOG_TITLE),
            ok=self._text(keys.SUCCESS_DIALOG_OK_BUTTON),
        )

    def attach(self, *, controller: MagiskPatchControllerPort) -> None:
        self._controller = controller

    def _require_controller(self) -> MagiskPatchControllerPort:
        if self._controller is None:
            raise RuntimeError("MagiskPatchControllerPort is not attached")
        return self._controller

    def choose_magisk_apk(self) -> None:
        file_path = self._choose_file(
            title=self._text(keys.SELECT_APK_DIALOG_TITLE),
            filetypes=(
                (self._text(keys.SELECT_APK_DIALOG_APK_FILES), "*.apk"),
                (self._text(keys.SELECT_APK_DIALOG_ALL_FILES), "*.*"),
            ),
        )
        if file_path:
            self.magisk_apk.set(file_path)
            try:
                architectures = self._require_controller().get_arches(file_path)
            except Exception as exc:
                self._warn(
                    self._text(keys.ARCHITECTURE_READ_FAILED_MESSAGE).format(error=exc)
                )
            else:
                if architectures:
                    self._arch_choices = build_choice_set(
                        self._language, tuple(architectures)
                    )
                    self.archs.configure(values=self._arch_choices.labels)
                    self.archs.current(0)
        self.lift()
        self.focus_force()

    def choose_boot_image(self) -> None:
        selected = self._choose_file(
            title=self._text(keys.SELECT_BOOT_DIALOG_TITLE),
            filetypes=(
                (self._text(keys.SELECT_BOOT_DIALOG_IMAGE_FILES), "*.img *.bin"),
                (self._text(keys.SELECT_BOOT_DIALOG_ALL_FILES), "*.*"),
            ),
        )
        if selected:
            self.boot_file.set(selected)

    def _set_running(self, running: bool) -> None:
        self.patch_button.configure(
            state="disabled" if running else "normal",
            text=self._text(keys.RUNNING_BUTTON if running else keys.PATCH_BUTTON),
        )

    def patch(self) -> None:
        controller = self._require_controller()
        boot_file_path = self.boot_file.get()
        magisk_apk_path = self.magisk_apk.get()
        ok, message = controller.validate(
            boot_file_path=boot_file_path,
            magisk_apk_path=magisk_apk_path,
        )
        if not ok:
            self._warn(message)
            return
        self._set_running(True)
        controller.start(
            boot_file_path=boot_file_path,
            magisk_apk_path=magisk_apk_path,
            is_64bit=self.IS64BIT.get(),
            keep_verity=self.KEEPVERITY.get(),
            keep_force_encrypt=self.KEEPFORCEENCRYPT.get(),
            recovery_mode=self.RECOVERYMODE.get(),
            arch=self._arch_choices.value_at(self.archs.current()),
            on_success=self._handle_success,
            on_error=self._handle_error,
        )

    def _handle_success(self, result: str) -> None:
        self._inform(self._text(keys.SUCCESS_MESSAGE).format(path=result))
        self._set_running(False)

    def _handle_error(self, exc: Exception) -> None:
        logging.exception("Magisk patching error")
        self._warn(self._text(keys.FAILURE_MESSAGE).format(error=exc))
        self._set_running(False)

    def _build_ui(self) -> None:
        ttk.Label(self, text=self._text(keys.HEADING)).pack(pady=(5, 10))

        boot_frame = ttk.Frame(self)
        boot_frame.pack(fill=X, padx=5, pady=2)
        ttk.Label(
            boot_frame,
            text=self._text(keys.BOOT_IMAGE_LABEL),
            width=12,
        ).pack(side=LEFT, padx=(0, 5), pady=5)
        ttk.Entry(boot_frame, textvariable=self.boot_file).pack(
            side=LEFT,
            padx=5,
            pady=5,
            expand=True,
            fill=X,
        )
        ttk.Button(
            boot_frame,
            text=self._text(keys.BOOT_IMAGE_BROWSE_BUTTON),
            command=self.choose_boot_image,
        ).pack(side=LEFT, padx=(5, 0), pady=5)

        apk_frame = ttk.Frame(self)
        apk_frame.pack(fill=X, padx=5, pady=2)
        ttk.Label(
            apk_frame,
            text=self._text(keys.MAGISK_APK_LABEL),
            width=12,
        ).pack(side=LEFT, padx=(0, 5), pady=5)
        ttk.Entry(apk_frame, textvariable=self.magisk_apk).pack(
            side=LEFT,
            padx=5,
            pady=5,
            expand=True,
            fill=X,
        )
        ttk.Button(
            apk_frame,
            text=self._text(keys.MAGISK_APK_BROWSE_BUTTON),
            command=self.choose_magisk_apk,
        ).pack(side=LEFT, padx=(5, 0), pady=5)

        arch_frame = ttk.Frame(self)
        arch_frame.pack(fill=X, padx=5, pady=2)
        ttk.Label(
            arch_frame,
            text=self._text(keys.ARCHITECTURE_LABEL),
            width=12,
        ).pack(side=LEFT, padx=(0, 5), pady=5)
        self.archs = ttk.Combobox(
            arch_frame,
            state="readonly",
            textvariable=self.magisk_arch,
            values=self._arch_choices.labels,
        )
        self.archs.current(self._arch_choices.index_for("arm64-v8a"))
        self.archs.pack(side=LEFT, padx=5, pady=5, expand=True, fill=X)

        self.IS64BIT = BooleanVar(value=True)
        self.KEEPVERITY = BooleanVar(value=False)
        self.KEEPFORCEENCRYPT = BooleanVar(value=False)
        self.RECOVERYMODE = BooleanVar(value=False)

        first_options = ttk.Frame(self)
        first_options.pack(fill=X, padx=5, pady=2)
        ttk.Checkbutton(
            first_options,
            text=self._text(keys.IS_64BIT_OPTION_LABEL),
            variable=self.IS64BIT,
        ).pack(padx=5, pady=2, side=LEFT)
        ttk.Checkbutton(
            first_options,
            text=self._text(keys.KEEP_VERITY_OPTION_LABEL),
            variable=self.KEEPVERITY,
        ).pack(padx=5, pady=2, side=LEFT)

        second_options = ttk.Frame(self)
        second_options.pack(fill=X, padx=5, pady=2)
        ttk.Checkbutton(
            second_options,
            text=self._text(keys.KEEP_FORCE_ENCRYPT_OPTION_LABEL),
            variable=self.KEEPFORCEENCRYPT,
        ).pack(padx=5, pady=2, side=LEFT)
        ttk.Checkbutton(
            second_options,
            text=self._text(keys.RECOVERY_MODE_OPTION_LABEL),
            variable=self.RECOVERYMODE,
        ).pack(padx=5, pady=2, side=LEFT)

        self.patch_button = ttk.Button(
            self,
            text=self._text(keys.PATCH_BUTTON),
            style="Accent.TButton",
            command=self.patch,
        )
        self.patch_button.pack(fill=X, padx=5, pady=(10, 5))


__all__ = ["MagiskPatcher"]
