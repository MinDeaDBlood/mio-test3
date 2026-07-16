from __future__ import annotations

from tkinter import StringVar

from src.app.animated_tasks import AnimatedTaskRunner
from src.app.project_state import current_project_state
from src.app.runtime.contract import BOOTSTRAP_WINDOW_KEYS, validate_runtime_keys
from src.app.runtime.core_access import require_project_manager
from src.app.runtime.models import BootstrapWindowRuntime
from src.app.runtime.phases import register_bootstrap_window_runtime
from src.app.ui_scheduler import initialize_app_ui_scheduler
from src.ui.common.loading_animation import LoadingAnimation


def initialize_window_runtime(main_window) -> BootstrapWindowRuntime:
    """Create and register the complete runtime required by Tk windows."""
    animation = AnimatedTaskRunner(LoadingAnimation())
    animation.master = main_window

    current_project_name = StringVar(master=main_window)
    current_project_state.bind(current_project_name)
    require_project_manager().bind_current_project_name(current_project_name)

    theme = StringVar(master=main_window)
    language = StringVar(master=main_window)
    ui_scheduler = initialize_app_ui_scheduler(main_window)

    register_bootstrap_window_runtime(
        main_window=main_window,
        animation=animation,
        ui_scheduler=ui_scheduler,
        current_project_name=current_project_name,
        theme=theme,
        language=language,
    )
    validate_runtime_keys(BOOTSTRAP_WINDOW_KEYS, context='bootstrap window phase')
    return BootstrapWindowRuntime(
        main_window=main_window,
        animation=animation,
        ui_scheduler=ui_scheduler,
        current_project_name=current_project_name,
        theme=theme,
        language=language,
    )


__all__ = ['initialize_window_runtime']
