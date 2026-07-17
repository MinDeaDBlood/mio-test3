from __future__ import annotations

import logging
import sys
from collections.abc import Callable

from src.app.background_jobs import start_background_job
from src.app.runtime.contexts.plugins import resolve_plugin_lifecycle
from src.app.runtime.contexts.settings import resolve_animation
from src.app.runtime.contexts.tooling import resolve_tool_self
from src.app.runtime.contexts.ui import resolve_ui_host_window
from src.platform.process_restart import build_restart_argv, launch_replacement_process
from src.platform.crash_logging import flush_logging, operation_context


ConfirmRestart = Callable[[], bool]


def exit_tool() -> None:
    logging.getLogger(__name__).info('Application shutdown requested')
    with operation_context('lifecycle.plugin_shutdown'):
        resolve_plugin_lifecycle().shutdown()
    resolve_ui_host_window().destroy()
    flush_logging()


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
        replacement_pid = launch_replacement_process(argv)
        logging.getLogger(__name__).info(
            'Replacement process launched: pid=%s',
            replacement_pid,
        )

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
