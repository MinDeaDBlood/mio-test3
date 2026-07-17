from __future__ import annotations

import logging
from importlib import import_module

from src.app.composition.dialogs import ask_win, choose_directory
from src.app.localization_runtime import lang
from src.app.composition import settings_tab_keys as keys
from src.app.runtime.contexts.paths import resolve_prog_path, resolve_temp_path
from src.app.runtime.contexts.settings import (
    resolve_animation,
    resolve_settings,
    resolve_states,
)
from src.app.runtime.contexts.ui import (
    resolve_language,
    resolve_theme,
    resolve_ui_host_window,
)
from src.app.settings.actions import SettingsService
from src.platform.language_repository import list_language_names
from src.app.settings.runtime import SettingsRuntimeContext
from src.platform.system_shell import open_in_file_manager
from src.app.ui_feedback import build_ui_dispatcher, build_ui_notifier
from src.app.ui_tasks import build_ui_task_runner
from src.app.settings.tab_controller import SettingsTabController
from src.ui.common.restart_confirmation import confirm_restart_with_active_tasks
from src.ui.tabs.settings.appearance.actions import (
    apply_theme_appearance,
    apply_transparency_appearance,
)
from src.app.settings.presentation_controller import SettingsPresentationController
from src.ui.tabs.settings.view import build_settings_tab


def _open_updater():
    return import_module("src.app.update").open_updater()


def compose_settings_tab(window):
    runtime = SettingsRuntimeContext(
        settings_obj=resolve_settings(),
        cwd_path=resolve_prog_path(),
        temp_path=resolve_temp_path(),
        updater_func=_open_updater,
        theme_var=resolve_theme(),
        language_var=resolve_language(),
    )
    host_window = resolve_ui_host_window()
    animation = resolve_animation()
    notifier = build_ui_notifier(host_window=host_window)
    controller = SettingsTabController(
        settings_obj=runtime.settings_obj,
        temp_path=runtime.temp_path,
        list_languages=list_language_names,
    )
    runtime.theme_var.set(controller.get_theme_value())
    runtime.language_var.set(controller.get_language_value())
    dispatcher = build_ui_dispatcher(host_window=window)
    task_runner = build_ui_task_runner(
        dispatcher=dispatcher,
        is_alive=window.winfo_exists,
        logger=logging,
    )
    settings_service = SettingsService(
        settings=runtime.settings_obj,
        states=resolve_states(),
    )

    def report_settings_error(_context: str, exc: Exception) -> None:
        message = lang.resolve_optional(str(exc), default=str(exc))
        notifier.show(message, color="red")

    actions = SettingsPresentationController(
        service=settings_service,
        read_theme=runtime.theme_var.get,
        read_language=runtime.language_var.get,
        report_error=report_settings_error,
        apply_theme_appearance=lambda theme_id: apply_theme_appearance(
            window=host_window,
            animation=animation,
            theme_id=theme_id,
        ),
        apply_transparency_appearance=lambda enabled: apply_transparency_appearance(
            enabled=enabled,
            effect_alpha=runtime.settings_obj.barlevel,
        ),
        confirm_restart_language_change=lambda: bool(
            ask_win(lang.resolve_required_ui_text(keys.LANGUAGE_RESTART_CONFIRMATION))
        ),
        choose_work_path=choose_directory,
        apply_work_path_to_view=lambda folder: window.show_local.set(folder),
        restart_app=lambda: import_module("src.app.lifecycle").restart_app(
            confirm_unsaved=lambda: confirm_restart_with_active_tasks(texts=lang)
        ),
        launch_updater=_open_updater,
    )
    return build_settings_tab(
        window,
        texts=lang,
        runtime=runtime,
        controller=controller,
        actions=actions,
        task_runner=task_runner,
        open_work_path=lambda *_: open_in_file_manager(controller.get_work_path()),
        open_cache_path=lambda *_: open_in_file_manager(runtime.temp_path),
        confirm_context_patch=lambda: ask_win(
            lang.resolve_required_ui_text(keys.CONTEXT_PATCH_CONFIRMATION), is_top=True
        ),
    )


__all__ = ["compose_settings_tab"]
