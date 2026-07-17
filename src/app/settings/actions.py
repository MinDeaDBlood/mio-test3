from __future__ import annotations

from dataclasses import dataclass

from src.app.localization_selection import apply_language
from src.app.settings.theme import normalize_theme_id
from src.app.runtime.contexts.contracts import SettingsProtocol, StateBagProtocol

_TOGGLE_KEYS = frozenset({
    'error_helper_enabled',
    'magisk_not_decompress',
    'boot_skip_ramdisk',
    'auto_unpack',
    'treff',
})




def _normalize_confidence(value: str | int | float) -> str:
    try:
        normalized = int(round(float(value)))
    except (TypeError, ValueError) as exc:
        raise ValueError('error_helper_confidence_invalid') from exc
    if normalized < 50 or normalized > 100:
        raise ValueError('error_helper_confidence_out_of_range')
    return str(normalized)

def _normalize_switch(value: str | bool) -> str:
    if isinstance(value, bool):
        return '1' if value else '0'
    normalized = str(value).strip()
    if normalized not in {'0', '1'}:
        raise ValueError('settings_switch_value_invalid')
    return normalized


@dataclass(frozen=True)
class SettingsService:
    """Persist validated settings without depending on Tk widgets."""

    settings: SettingsProtocol
    states: StateBagProtocol

    def set_theme(self, theme_id: str) -> None:
        self.settings.set_value('theme', normalize_theme_id(theme_id))

    def set_language(self, language_name: str) -> bool:
        normalized = str(language_name).strip()
        if not normalized:
            raise ValueError('settings_language_required')
        apply_language(self.settings, normalized)
        return not bool(self.states.in_oobe)

    def set_work_path(self, folder: str) -> None:
        normalized = str(folder).strip()
        if not normalized:
            raise ValueError('settings_work_path_required')
        self.settings.set_value('path', normalized)

    def set_toggle(self, key: str, value: str | bool) -> str:
        if key not in _TOGGLE_KEYS:
            raise ValueError('settings_unsupported_toggle')
        normalized = _normalize_switch(value)
        self.settings.set_value(key, normalized)
        return normalized

    def set_transparency_enabled(self, enabled: bool) -> None:
        self.set_toggle('treff', enabled)

    def set_error_helper_confidence(self, value: str | int | float) -> str:
        normalized = _normalize_confidence(value)
        self.settings.set_value('error_helper_confidence', normalized)
        return normalized

    def set_auto_update(self, value: str | bool) -> None:
        self.settings.set_value('check_upgrade', _normalize_switch(value))


def apply_welcome_language(*, settings: SettingsProtocol, language_name: str) -> None:
    apply_language(settings, language_name)


__all__ = ['SettingsService', 'apply_welcome_language']
