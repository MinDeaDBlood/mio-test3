from __future__ import annotations

HOME_TAB = "main_window_composition_home"
PROJECT_TAB = "main_window_composition_project"
SETTINGS_TAB = "main_window_composition_settings"
ABOUT_TAB = "main_window_composition_about"
TASKS_TAB = "main_window_composition_tasks"
TOOLBOX_TAB = "toolbox"
RIGHT_PANEL_CLEAR_ACTION = "main_window_composition_clear_action"

ALL_REQUIRED_KEYS = (
    HOME_TAB,
    PROJECT_TAB,
    SETTINGS_TAB,
    ABOUT_TAB,
    TASKS_TAB,
    TOOLBOX_TAB,
    RIGHT_PANEL_CLEAR_ACTION,
)

__all__ = [name for name in globals() if name.isupper()]
