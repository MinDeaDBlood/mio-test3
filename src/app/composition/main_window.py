from __future__ import annotations

import logging
from dataclasses import dataclass

from src.app.composition.log_stream import create_stdout_redirector
from src.app.composition.main_tabs import compose_main_tabs
from src.app.composition.settings_tab import compose_settings_tab
from src.app.input_actions import choose_and_dispatch_input_file, dispatch_input_paths
from src.app.localization import ensure_selected_language_loaded
from src.app.localization_runtime import lang
from src.app.composition import main_window_keys as keys
from src.app.plugins.manager_host import PluginManagerHost, install_lazy_plugin_manager_host
from src.app.pro_runtime import is_pro
from src.app.projects.host import ProjectWorkspaceHost, install_lazy_project_workspace_host
from src.app.std_streams import ensure_process_streams_installed, get_stdout_router
from src.platform.runtime_environment import detect_runtime_warning_codes
from src.ui.common.dnd import DND_FILES
from src.ui.window_sections.main_window_layout import fit_main_window_to_content
from src.ui.window_sections.main_window_presenter import render_startup_warning
from src.ui.window_sections.panels import build_notebook_shell, build_right_panel
from src.ui.window_sections.right_panel_presenter import RightPanelController


@dataclass(frozen=True)
class MainWindowComposition:
    project_workspace_host: ProjectWorkspaceHost
    plugin_manager_host: PluginManagerHost

    @property
    def project_menu(self):
        return self.project_workspace_host.project_menu

    @property
    def unpack_view(self):
        return self.project_workspace_host.unpack_view


def _bind_output_streams(window) -> None:
    stdout_sink = create_stdout_redirector(window.show, stdout=True)
    stderr_sink = create_stdout_redirector(window.show, error_mode=True, stderr=True)
    window._stdout_sink = stdout_sink
    window._stderr_sink = stderr_sink


def create_main_window():
    """Create the main window with all presentation dependencies injected."""
    from src.core.paths import prog_path
    from src.ui.main_window import Tool

    return Tool(texts=lang, tkdnd_library_root=prog_path)


def compose_main_window(window) -> MainWindowComposition:
    """Attach application services and build the complete main-window UI."""
    ensure_selected_language_loaded(*keys.ALL_REQUIRED_KEYS)
    startup_warnings = tuple(
        warning
        for code in detect_runtime_warning_codes()
        if (warning := render_startup_warning(code, texts=lang)) is not None
    )
    build_notebook_shell(window, pro_enabled=is_pro, texts=lang)
    compose_main_tabs(window)
    compose_settings_tab(window)
    project_workspace_host = install_lazy_project_workspace_host(window)
    plugin_manager_host = install_lazy_plugin_manager_host(window)

    ensure_process_streams_installed()
    right_panel = RightPanelController(lang=lang, stdout_obj=get_stdout_router())
    build_right_panel(
        window,
        spec=right_panel.build_spec(),
        clear_text=lang.resolve_required_ui_text(keys.RIGHT_PANEL_CLEAR_ACTION),
        choose_input_file=choose_and_dispatch_input_file,
        dispatch_input_paths=dispatch_input_paths,
        bind_output_streams=_bind_output_streams,
        dnd_files=DND_FILES,
    )
    refresh_focusability = getattr(window.notepad, "refresh_focusability", None)
    if callable(refresh_focusability):
        refresh_focusability()
    fit_main_window_to_content(window)
    for warning in startup_warnings:
        logging.warning("%s", warning.message)
    return MainWindowComposition(
        project_workspace_host=project_workspace_host,
        plugin_manager_host=plugin_manager_host,
    )


__all__ = ["MainWindowComposition", "compose_main_window", "create_main_window"]
