from __future__ import annotations

import logging

from src.app.runtime.contexts.settings import resolve_settings, resolve_states
from src.app.runtime.contexts.tooling import resolve_tool_self
from src.app.runtime.contexts.ui import resolve_ui_host_window
from src.app.ui_feedback import build_ui_dispatcher
from src.app.ui_tasks import build_ui_task_runner
from src.app.update_controller import UpdateWorkflowController
from src.ui.update.presenter import UpdatePresentationController
from src.app.update_runtime import fetch_current_release_check, resolve_update_url
from src.app.localization_runtime import lang
from src.core.paths import prog_path
from src.app.update_orchestrator import UpdateOrchestrator
from src.ui.update.window import UpdaterWindow
from src.platform.runtime_paths import UPDATE_TEMP_DIR


def open_update_window(*, auto_start: bool = True):
    states = resolve_states()
    if states.update_window:
        raise RuntimeError("Updater window is already active")
    settings = resolve_settings()
    host_window = resolve_ui_host_window()
    orchestrator = UpdateOrchestrator(
        settings=settings,
        states=states,
        cwd_path=prog_path,
        temp_path=str(UPDATE_TEMP_DIR),
        tool_self_path=resolve_tool_self(),
    )
    holder: dict[str, UpdatePresentationController] = {}
    view = UpdaterWindow(
        version=settings.version,
        texts=lang,
        source_mode=bool(states.run_source),
        source_update_available=orchestrator.can_pull_source_repository(),
        on_update_requested=lambda: holder["controller"].request_update(),
        on_close_requested=lambda: holder["controller"].close(),
    )
    states.update_window = True
    dispatcher = build_ui_dispatcher(host_window=view)
    workflow = UpdateWorkflowController(
        settings=settings,
        states=states,
        orchestrator=orchestrator,
        task_runner=build_ui_task_runner(
            dispatcher=dispatcher, is_alive=view.winfo_exists, logger=logging
        ),
        dispatcher=dispatcher,
        update_url=resolve_update_url(),
        fetch_release=fetch_current_release_check,
    )
    controller = UpdatePresentationController(
        view=view,
        host_window=host_window,
        settings=settings,
        states=states,
        workflow=workflow,
        texts=lang,
    )
    holder["controller"] = controller
    view.controller = controller
    if auto_start and view.is_ready():
        controller.start()
    return view


__all__ = ["open_update_window"]
