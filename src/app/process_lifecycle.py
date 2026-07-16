from __future__ import annotations

import logging
import sys
from collections.abc import Callable

from src.app.background_jobs import start_background_job
from src.app.runtime.contexts.plugins import resolve_module_manager
from src.app.runtime.contexts.settings import resolve_animation
from src.app.runtime.contexts.tooling import resolve_tool_self
from src.app.runtime.contexts.ui import resolve_ui_host_window
from src.platform.process_restart import build_restart_argv, run_replacement_process


ConfirmRestart = Callable[[], bool]


def exit_tool() -> None:
    module_manager = resolve_module_manager()
    module_manager.addon_loader.run_entry(module_manager.addon_entries.close)
    resolve_ui_host_window().destroy()


def restart(window=None, *, confirm_unsaved: ConfirmRestart | None = None) -> bool:
    animation = resolve_animation()
    if animation.has_tasks():
        if confirm_unsaved is None:
            raise RuntimeError('Restart with active tasks requires an explicit confirmation callback.')
        if not confirm_unsaved():
            return False

    def launch_replacement() -> None:
        argv = build_restart_argv(
            tool_self=resolve_tool_self(),
            original_argv=sys.argv,
        )
        raise SystemExit(run_replacement_process(argv))

    if window is not None:
        window.destroy()

    main_window = resolve_ui_host_window()
    for child in tuple(main_window.winfo_children()):
        try:
            child.destroy()
        except Exception:
            logging.exception('Cannot destroy child window during restart: %r', child)
    main_window.destroy()
    start_background_job(launch_replacement, daemon=False)
    return True


__all__ = ['exit_tool', 'restart']
