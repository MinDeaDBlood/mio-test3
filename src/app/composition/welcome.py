from __future__ import annotations

from src.app.composition.dialogs import choose_directory
from src.app.localization_runtime import lang
from src.app.runtime.contexts.settings import resolve_settings, resolve_states
from src.app.runtime.contexts.ui import resolve_language, resolve_ui_host_window
from src.app.settings.actions import apply_welcome_language
from src.platform.system_shell import open_in_file_manager
from src.app.welcome.actions import WelcomeActions
from src.app.welcome.controller import WelcomeController
from src.platform.welcome_content_repository import WelcomeContentRepository


def build_welcome_controller(*, frame_count: int) -> WelcomeController:
    settings = resolve_settings()
    language_var = resolve_language()
    return WelcomeController(
        settings=settings,
        content_service=WelcomeContentRepository(),
        current_language=language_var.get,
        frame_count=frame_count,
    )


def open_welcome():
    from src.ui.welcome.wizard import Welcome

    settings = resolve_settings()
    states = resolve_states()
    language_var = resolve_language()
    main_window = resolve_ui_host_window()
    frame_count = 6
    controller = WelcomeController(
        settings=settings,
        content_service=WelcomeContentRepository(),
        current_language=language_var.get,
        frame_count=frame_count,
    )
    actions = WelcomeActions(
        choose_workdir=choose_directory,
        open_workdir=open_in_file_manager,
        apply_language=lambda name: apply_welcome_language(
            settings=settings, language_name=name
        ),
        set_oobe_active=lambda active: setattr(states, "in_oobe", bool(active)),
    )
    return Welcome(
        main_window=main_window,
        controller=controller,
        language_var=language_var,
        actions=actions,
        texts=lang,
    )


__all__ = ["build_welcome_controller", "open_welcome"]
