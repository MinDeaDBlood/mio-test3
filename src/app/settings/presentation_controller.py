from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol


class SettingsServicePort(Protocol):
    def set_theme(self, theme_name: str) -> None: ...
    def set_language(self, language_name: str) -> bool: ...
    def set_work_path(self, folder: str) -> None: ...
    def set_toggle(self, key: str, value: str | bool) -> str: ...
    def set_auto_update(self, value: str | bool) -> None: ...
    def set_error_helper_confidence(self, value: str | int | float) -> str: ...


ErrorReporter = Callable[[str, Exception], object]


@dataclass(frozen=True)
class SettingsPresentationController:
    """Coordinate settings actions without importing Tk or UI modules."""

    service: SettingsServicePort
    read_theme: Callable[[], object]
    read_language: Callable[[], object]
    report_error: ErrorReporter
    apply_theme_appearance: Callable[[str], object]
    apply_transparency_appearance: Callable[[bool], object]
    confirm_restart_language_change: Callable[[], bool]
    choose_work_path: Callable[[], str]
    apply_work_path_to_view: Callable[[str], object]
    restart_app: Callable[[], object]
    launch_updater: Callable[[], object]

    def _handle_error(self, context: str, exc: Exception) -> None:
        logging.exception("%s", context)
        self.report_error(context, exc)

    def apply_theme(self) -> None:
        theme_name = str(self.read_theme())
        try:
            self.service.set_theme(theme_name)
            self.apply_theme_appearance(theme_name)
        except Exception as exc:
            self._handle_error(f"settings.theme.apply_failed: theme={theme_name}", exc)

    def apply_toggle(self, key: str, value: str) -> None:
        try:
            normalized = self.service.set_toggle(key, value)
            if key == "treff":
                self.apply_transparency_appearance(normalized == "1")
        except Exception as exc:
            self._handle_error(
                f"settings.toggle.apply_failed: key={key} value={value}", exc
            )

    def apply_transparency(self, value: str) -> None:
        self.apply_toggle("treff", value)

    def apply_error_helper_confidence(self, value: str) -> None:
        try:
            self.service.set_error_helper_confidence(value)
        except Exception as exc:
            self._handle_error(
                f"settings.error_helper_confidence.apply_failed: value={value}", exc
            )

    def apply_auto_update(self, value: str) -> None:
        try:
            self.service.set_auto_update(value)
        except Exception as exc:
            self._handle_error(f"settings.auto_update.apply_failed: value={value}", exc)

    def apply_language(self) -> None:
        language_name = str(self.read_language())
        try:
            restart_required = self.service.set_language(language_name)
        except Exception as exc:
            self._handle_error(
                f"settings.language.apply_failed: language={language_name}", exc
            )
            return
        if restart_required and self.confirm_restart_language_change():
            self.restart_app()

    def choose_and_apply_work_path(self) -> None:
        try:
            folder = self.choose_work_path()
            if not folder:
                return
            self.service.set_work_path(folder)
            self.apply_work_path_to_view(folder)
        except Exception as exc:
            self._handle_error("settings.work_path.apply_failed", exc)

    def open_updater(self) -> None:
        try:
            self.launch_updater()
        except Exception as exc:
            self._handle_error("settings.updater.launch_failed", exc)


__all__ = ["ErrorReporter", "SettingsPresentationController", "SettingsServicePort"]
