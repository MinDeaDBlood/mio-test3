from __future__ import annotations

from dataclasses import dataclass

from src.ui.localization import LocalizationCatalog


@dataclass(frozen=True)
class MainTabTitleKeys:
    home: str = "registry_home"
    project: str = "registry_project"
    plugins: str = "registry_plugin"
    settings: str = "registry_settings"
    about: str = "registry_about"
    tasks: str = "registry_tasks"
    tools: str = "toolbox"


MAIN_TAB_TITLE_KEYS = MainTabTitleKeys()


def main_tab_title(texts: LocalizationCatalog, tab_name: str) -> str:
    key = getattr(MAIN_TAB_TITLE_KEYS, tab_name)
    return texts.resolve_required_ui_text(key)


__all__ = ["MAIN_TAB_TITLE_KEYS", "MainTabTitleKeys", "main_tab_title"]
