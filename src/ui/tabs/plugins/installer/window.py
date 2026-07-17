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


class PluginInstallerWindow(Toplevel):
    """MPK installer view. Package operations are delegated to the controller."""

    def __init__(
        self, mpk_path: str, *, texts: LocalizationCatalog, controller, error_codes
    ):
        super().__init__()
        self._texts = texts
        self.controller = controller
        self.error_codes = error_codes
        self.package_info: PluginPackageInfoProtocol | None = None
        self.package_path = mpk_path
        self.title(self._texts.resolve_required_ui_text(keys.PLUGINS_INSTALLER_WINDOW_PLUGIN_INSTALLATION_TITLE))
        self._build_view()
        self.load()
        self.center_on_screen(force=True)
        self.wait_window()
        self.controller.notify_catalog_changed()

    def _build_view(self) -> None:
        info_frame = Frame(self)
        self.logo_label = Label(info_frame)
        self.logo_label.pack(padx=10, pady=10)
        self.name_label = Label(info_frame, font=(None, 14))
        self.name_label.pack(padx=10, pady=10)
        self.version_label = Label(info_frame, font=(None, 12))
        self.version_label.pack(padx=10, pady=10)
        self.author_label = Label(info_frame, font=(None, 12))
        self.author_label.pack(padx=10, pady=10)
        info_frame.pack(side=LEFT)
        self.description_text = Text(self, width=50, height=20)
        self.description_text.pack(padx=10, pady=10)
        self.progress_bar = ttk.Progressbar(
            self,
            length=200,
            mode="indeterminate",
            orient=HORIZONTAL,
            maximum=100,
            value=0,
        )
        self.progress_bar.pack()
        self.status_label = Label(
            self, text=self._texts.resolve_required_ui_text(keys.PLUGINS_INSTALLER_WINDOW_READY), font=(None, 12)
        )
        self.status_label.pack(padx=10, pady=10)
        self.install_button = ttk.Button(
            self,
            text=self._texts.resolve_required_ui_text(keys.PLUGINS_INSTALLER_WINDOW_INSTALL_ACTION),
            style="Accent.TButton",
            command=self.request_install,
        )
        self.install_button.pack(padx=10, pady=10, expand=True, fill=X)

    def request_install(self):
        if self.install_button.cget("text") == self._texts.resolve_required_ui_text(keys.PLUGINS_INSTALLER_WINDOW_FINISH):
            self.destroy()
            return
        if self.package_info is None:
            return
        self.progress_bar.start()
        self.install_button.config(state=DISABLED)
        self.controller.install(
            self.package_path,
            on_success=lambda result: self._apply_install_result(*result),
            on_error=self._handle_install_failure,
        )

    def _handle_install_failure(self, exc: Exception):
        logging.error(
            "Plugin installer request failed", exc_info=(type(exc), exc, exc.__traceback__)
        )
        self._apply_install_result(self.error_codes.IsBroken, str(exc))

    def _apply_install_result(self, result_code, reason):
        if not self.winfo_exists():
            return
        plugin_name = self.package_info.name if self.package_info is not None else ""
        if result_code == self.error_codes.ArchNotSupported:
            self.status_label["text"] = reason
        elif result_code == self.error_codes.PlatformNotSupport:
            self.status_label["text"] = self._texts.resolve_required_ui_text(
                keys.UNSUPPORTED_PLATFORM_MESSAGE_FORMAT
            ).format(platform.system())
        elif result_code == self.error_codes.DependsMissing:
            self.status_label["text"] = (
                self._texts.resolve_required_ui_text(keys.PLUGINS_INSTALLER_WINDOW_PLUGIN_DEPENDENCY_MISSING_FORMAT)
                % (plugin_name, reason, reason)
            )
            self.install_button["text"] = self._texts.resolve_required_ui_text(keys.PLUGINS_INSTALLER_WINDOW_RETRY)
            self.install_button.config(state="normal")
        elif result_code == self.error_codes.IsBroken:
            self.status_label["text"] = reason or self._texts.resolve_required_ui_text(
                keys.BROKEN_PACKAGE_MESSAGE
            )
            self.install_button["text"] = self._texts.resolve_required_ui_text(keys.PLUGINS_INSTALLER_WINDOW_RETRY)
            self.install_button.config(state="normal")
        elif result_code == self.error_codes.Normal:
            self.status_label["text"] = (
                self._texts.resolve_required_ui_text(keys.PLUGINS_INSTALLER_WINDOW_INSTALLATION_COMPLETE)
            )
            self.install_button["text"] = self._texts.resolve_required_ui_text(keys.PLUGINS_INSTALLER_WINDOW_FINISH)
            self.install_button.config(state="normal")
        self.progress_bar.stop()
        self.progress_bar["mode"] = "determinate"
        self.progress_bar["value"] = 100

    def load(self):
        try:
            self.package_info = self.controller.read_package(self.package_path)
            self.package_icon_photo = self._build_icon(self.package_info.icon_data)
        except Exception as exc:
            logging.exception("Unable to read MPK package")
            self.unavailable(str(exc))
            return
        self.name_label.config(text=self.package_info.name)
        self.logo_label.config(image=self.package_icon_photo)
        self.author_label.config(
            text=self._texts.resolve_required_ui_text(keys.PLUGINS_INSTALLER_WINDOW_AUTHOR_FORMAT).format(
                self.package_info.author
            )
        )
        self.version_label.config(
            text=self._texts.resolve_required_ui_text(keys.PLUGINS_INSTALLER_WINDOW_VERSION_FORMAT).format(
                self.package_info.version
            )
        )
        self.description_text.insert("insert", self.package_info.description)

    @staticmethod
    def _build_icon(icon_data: bytes | None):
        return (
            _photo_image(data=images.placeholder_image)
            if icon_data is None
            else _decode_icon_photo(icon_data)
        )

    def unavailable(self, reason: str):
        self.package_info = None
        self.package_icon_photo = _photo_image(data=images.error_logo)
        self.name_label.config(
            text=self._texts.resolve_required_ui_text(keys.UNAVAILABLE_PACKAGE_NAME),
            foreground="yellow",
        )
        self.logo_label.config(image=self.package_icon_photo)
        self.author_label.destroy()
        self.version_label.destroy()
        self.progress_bar.destroy()
        self.status_label.config(text=reason)
        self.install_button.config(state=DISABLED)


__all__ = ["PluginInstallerWindow"]
