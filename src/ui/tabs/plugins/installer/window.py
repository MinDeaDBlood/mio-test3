from __future__ import annotations

import logging
import platform
from io import BytesIO
from typing import Protocol
from tkinter import DISABLED, HORIZONTAL, LEFT, X, Frame, Label, Text, ttk

from src.ui.localization import LocalizationCatalog
from src.ui.assets import images
from src.ui.common.windowing import Toplevel
from src.ui.tabs.plugins.installer import keys


class PluginPackageInfoProtocol(Protocol):
    name: str
    version: str
    author: str
    description: str
    icon_data: bytes | None


def _photo_image(*args, **kwargs):
    from PIL.ImageTk import PhotoImage

    return PhotoImage(*args, **kwargs)


def _decode_icon_photo(raw_icon: bytes):
    from PIL.Image import open as open_img

    return _photo_image(open_img(BytesIO(raw_icon)).resize((128, 128)))


class InstallMpk(Toplevel):
    """MPK installer view. Package operations are delegated to the controller."""

    def __init__(
        self, mpk_path: str, *, texts: LocalizationCatalog, controller, error_codes
    ):
        super().__init__()
        self._texts = texts
        self.controller = controller
        self.error_codes = error_codes
        self.package_info: PluginPackageInfoProtocol | None = None
        self.mpk = mpk_path
        self.title(self._texts.resolve_required_ui_text(keys.PLUGINS_INSTALLER_WINDOW_PLUGIN_INSTALLATION_TITLE))
        self._build_view()
        self.load()
        self.center_on_screen(force=True)
        self.wait_window()
        self.controller.notify_catalog_changed()

    def _build_view(self) -> None:
        info_frame = Frame(self)
        self.logo = Label(info_frame)
        self.logo.pack(padx=10, pady=10)
        self.name_label = Label(info_frame, font=(None, 14))
        self.name_label.pack(padx=10, pady=10)
        self.version = Label(info_frame, font=(None, 12))
        self.version.pack(padx=10, pady=10)
        self.author = Label(info_frame, font=(None, 12))
        self.author.pack(padx=10, pady=10)
        info_frame.pack(side=LEFT)
        self.text = Text(self, width=50, height=20)
        self.text.pack(padx=10, pady=10)
        self.prog = ttk.Progressbar(
            self,
            length=200,
            mode="indeterminate",
            orient=HORIZONTAL,
            maximum=100,
            value=0,
        )
        self.prog.pack()
        self.state = Label(
            self, text=self._texts.resolve_required_ui_text(keys.PLUGINS_INSTALLER_WINDOW_READY), font=(None, 12)
        )
        self.state.pack(padx=10, pady=10)
        self.installb = ttk.Button(
            self,
            text=self._texts.resolve_required_ui_text(keys.PLUGINS_INSTALLER_WINDOW_INSTALL_ACTION),
            style="Accent.TButton",
            command=self.request_install,
        )
        self.installb.pack(padx=10, pady=10, expand=True, fill=X)

    def request_install(self):
        if self.installb.cget("text") == self._texts.resolve_required_ui_text(keys.PLUGINS_INSTALLER_WINDOW_FINISH):
            self.destroy()
            return
        if self.package_info is None:
            return
        self.prog.start()
        self.installb.config(state=DISABLED)
        self.controller.install(
            self.mpk,
            on_success=lambda result: self._apply_install_result(*result),
            on_error=self._handle_install_failure,
        )

    def _handle_install_failure(self, exc: Exception):
        logging.error(
            "InstallMpk request failed", exc_info=(type(exc), exc, exc.__traceback__)
        )
        self._apply_install_result(self.error_codes.IsBroken, str(exc))

    def _apply_install_result(self, ret, reason):
        if not self.winfo_exists():
            return
        plugin_name = self.package_info.name if self.package_info is not None else ""
        if ret == self.error_codes.ArchNotSupported:
            self.state["text"] = reason
        elif ret == self.error_codes.PlatformNotSupport:
            self.state["text"] = self._texts.resolve_required_ui_text(
                keys.UNSUPPORTED_PLATFORM_MESSAGE_FORMAT
            ).format(platform.system())
        elif ret == self.error_codes.DependsMissing:
            self.state["text"] = (
                self._texts.resolve_required_ui_text(keys.PLUGINS_INSTALLER_WINDOW_PLUGIN_DEPENDENCY_MISSING_FORMAT)
                % (plugin_name, reason, reason)
            )
            self.installb["text"] = self._texts.resolve_required_ui_text(keys.PLUGINS_INSTALLER_WINDOW_RETRY)
            self.installb.config(state="normal")
        elif ret == self.error_codes.IsBroken:
            self.state["text"] = reason or self._texts.resolve_required_ui_text(
                keys.BROKEN_PACKAGE_MESSAGE
            )
            self.installb["text"] = self._texts.resolve_required_ui_text(keys.PLUGINS_INSTALLER_WINDOW_RETRY)
            self.installb.config(state="normal")
        elif ret == self.error_codes.Normal:
            self.state["text"] = (
                self._texts.resolve_required_ui_text(keys.PLUGINS_INSTALLER_WINDOW_INSTALLATION_COMPLETE)
            )
            self.installb["text"] = self._texts.resolve_required_ui_text(keys.PLUGINS_INSTALLER_WINDOW_FINISH)
            self.installb.config(state="normal")
        self.prog.stop()
        self.prog["mode"] = "determinate"
        self.prog["value"] = 100

    def load(self):
        try:
            self.package_info = self.controller.read_package(self.mpk)
            self.pyt = self._build_icon(self.package_info.icon_data)
        except Exception as exc:
            logging.exception("Unable to read MPK package")
            self.unavailable(str(exc))
            return
        self.name_label.config(text=self.package_info.name)
        self.logo.config(image=self.pyt)
        self.author.config(
            text=self._texts.resolve_required_ui_text(keys.PLUGINS_INSTALLER_WINDOW_AUTHOR_FORMAT).format(
                self.package_info.author
            )
        )
        self.version.config(
            text=self._texts.resolve_required_ui_text(keys.PLUGINS_INSTALLER_WINDOW_VERSION_FORMAT).format(
                self.package_info.version
            )
        )
        self.text.insert("insert", self.package_info.description)

    @staticmethod
    def _build_icon(icon_data: bytes | None):
        return (
            _photo_image(data=images.none_byte)
            if icon_data is None
            else _decode_icon_photo(icon_data)
        )

    def unavailable(self, reason: str):
        self.package_info = None
        self.pyt = _photo_image(data=images.error_logo_byte)
        self.name_label.config(
            text=self._texts.resolve_required_ui_text(keys.UNAVAILABLE_PACKAGE_NAME),
            foreground="yellow",
        )
        self.logo.config(image=self.pyt)
        self.author.destroy()
        self.version.destroy()
        self.prog.destroy()
        self.state.config(text=reason)
        self.installb.config(state=DISABLED)


__all__ = ["InstallMpk"]
