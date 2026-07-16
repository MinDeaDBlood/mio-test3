from __future__ import annotations

from typing import Protocol
import tkinter as tk
from tkinter import ttk

from src.ui.localization import LocalizationCatalog
from src.ui.welcome.styles import WelcomeFonts


class WelcomeMainDataPort(Protocol):
    languages: tuple[str, ...]
    selected_language: str


class WelcomeWorkdirDataPort(Protocol):
    workdir: str


class WelcomeLicenseDataPort(Protocol):
    licenses: tuple[str, ...]
    selected_license: str
    license_text: str


class WelcomeControllerPort(Protocol):
    frame_count: int

    def main_data(self) -> WelcomeMainDataPort: ...
    def workdir_data(self) -> WelcomeWorkdirDataPort: ...
    def set_workdir(self, path: str) -> str: ...
    def license_data(self) -> WelcomeLicenseDataPort: ...
    def read_license(self, license_name: str) -> str: ...
    def read_private_notice(self) -> str: ...
    def initial_step(self) -> int: ...
    def persist_step(self, step: int) -> int: ...


class WelcomeActionsPort(Protocol):
    def choose_workdir(self) -> str: ...
    def open_workdir(self, path: str) -> object: ...
    def apply_language(self, language_name: str) -> object: ...
    def set_oobe_active(self, active: bool) -> object: ...



class WelcomeViewPort(Protocol):
    frame: ttk.Frame
    main_window: tk.Tk
    controller: WelcomeControllerPort
    language_var: tk.StringVar
    actions: WelcomeActionsPort
    texts: LocalizationCatalog
    fonts: WelcomeFonts
    content_wrap_width: int


__all__ = [
    'WelcomeActionsPort',
    'WelcomeControllerPort',
    'WelcomeLicenseDataPort',
    'WelcomeMainDataPort',
    'WelcomeViewPort',
    'WelcomeWorkdirDataPort',
]
