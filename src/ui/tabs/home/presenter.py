from __future__ import annotations

from src.ui.localization import LocalizationCatalog
from src.ui.tabs.home import keys


def build_home_welcome_text(texts: LocalizationCatalog, *args: str) -> str:
    template = texts.resolve_optional(keys.WELCOME_TEXT, default='')
    if template:
        try:
            return template % args
        except Exception:
            return str(template)
    return texts.resolve_required_ui_text(keys.WELCOME_FALLBACK_PRIMARY, keys.WELCOME_FALLBACK_SECONDARY)


__all__ = ['build_home_welcome_text']
