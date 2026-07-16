from __future__ import annotations

from pathlib import Path

from src.app.localization import load_language_from_files


def _settings_base_path(settings) -> Path:
    return Path(settings.set_file).resolve().parent.parent


def read_selected_language(settings) -> str:
    """Read and cache the selected language without loading presentation state."""
    selected_language = str(settings.language or '').strip()
    settings.config.read(settings.set_file, encoding='utf-8')
    if settings.config.has_section('setting') and settings.config.has_option('setting', 'language'):
        selected_language = settings.config.get('setting', 'language').strip()
        settings.language = selected_language
    if not selected_language:
        raise ValueError('Language name is empty')
    return selected_language


def load_selected_language(settings, *, base_path: str | Path | None = None) -> str:
    """Load the language selected in settings into the application localization runtime."""
    selected_language = read_selected_language(settings)
    return load_language_from_files(selected_language, base_path=base_path or _settings_base_path(settings))


def apply_language(settings, language_name: str, *, base_path: str | Path | None = None) -> str:
    """Persist and activate a language through the application layer."""
    resolved_name = str(language_name or '').strip()
    if not resolved_name:
        raise ValueError('Language name is empty')
    settings.set_value('language', resolved_name)
    return load_language_from_files(resolved_name, base_path=base_path or _settings_base_path(settings))


__all__ = ['apply_language', 'load_selected_language', 'read_selected_language']
