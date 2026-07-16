from __future__ import annotations

from collections.abc import Callable, Sequence

from src.app.runtime.contexts.contracts import SettingsProtocol
from src.core.cache_ops import calculate_directory_size, clear_directory


class SettingsTabController:
    """Coordinate settings persistence and application resource queries."""

    def __init__(
        self,
        *,
        settings_obj: SettingsProtocol,
        temp_path: str,
        list_languages: Callable[[], Sequence[str]],
    ) -> None:
        self.settings = settings_obj
        self.temp_path = temp_path
        self._list_languages = list_languages

    def get_work_path(self) -> str:
        return str(self.settings.path or "")

    def set_work_path(self, value: str) -> str:
        self.settings.set_value("path", value)
        return value

    def list_available_languages(self) -> tuple[str, ...]:
        return tuple(self._list_languages())

    def get_cache_size(self) -> int:
        return calculate_directory_size(self.temp_path)

    def clear_cache(self) -> int:
        return clear_directory(self.temp_path)

    def get_theme_value(self) -> str:
        return str(self.settings.theme)

    def get_language_value(self) -> str:
        return str(self.settings.language)

    def set_check_upgrade(self, value: str) -> None:
        self.settings.set_value("check_upgrade", value)

    @staticmethod
    def get_theme_choices() -> tuple[str, str]:
        return "light", "dark"

    def handle_context_patch_toggle(
        self,
        *,
        desired_value: str,
        confirm_enable: Callable[[], bool],
    ) -> tuple[str, bool]:
        if desired_value == "1" and not confirm_enable():
            self.settings.set_value("contextpatch", "0")
            return "0", False
        self.settings.set_value("contextpatch", desired_value)
        return desired_value, True

    def get_setting(self, key: str) -> str:
        return str(getattr(self.settings, key))

    def set_setting(self, key: str, value: str) -> None:
        self.settings.set_value(key, value)


__all__ = ["SettingsTabController"]
