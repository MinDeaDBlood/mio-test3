from __future__ import annotations

import logging

from src.app.localization_runtime import lang
from src.app.projects.pack.super_controller import SuperPackController
from src.app.projects.pack.super_runtime import (
    build_host_task_runner,
    build_pack_super_window_runtime,
    build_window_task_runner,
)
from src.logic.projects.pack.super.planning import DEFAULT_GROUP_NAME
from src.ui.tabs.project.pack.super.window import PackSuper


def open_super_pack_window():
    runtime = build_pack_super_window_runtime()
    view = PackSuper(
        texts=lang,
        default_group_name=DEFAULT_GROUP_NAME,
        emit=logging.info,
        master=runtime.host_window,
    )
    _window_dispatcher, window_task_runner = build_window_task_runner(window=view, logger=logging)
    _host_dispatcher, host_task_runner = build_host_task_runner(host_window=runtime.host_window, logger=logging)
    controller = SuperPackController(
        runtime=runtime,
        window_task_runner=window_task_runner,
        host_task_runner=host_task_runner,
        logger=logging,
    )
    def start_animation() -> None:
        host = runtime.host_window
        if host is not None and host.winfo_exists():
            host.update_idletasks()
        runtime.animation.run()

    view.attach_controller(
        controller,
        start_animation=start_animation,
        stop_animation=runtime.animation.stop,
        show_error=runtime.host_window.message_pop,
    )
    return view


__all__ = ['open_super_pack_window']
