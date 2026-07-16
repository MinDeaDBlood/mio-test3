from __future__ import annotations

from src.app.localization_runtime import lang
import logging

from src.app.project_contexts import build_app_boot_context
from src.app.projects.boot_images.controller import BootImageActionController
from src.app.ui_feedback import build_ui_dispatcher, build_ui_notifier
from src.app.ui_tasks import build_ui_task_runner
from src.logic.projects.pack.boot_images.service import run as run_pack
from src.logic.projects.unpack.boot_images.service import run as run_unpack
from src.app.composition.service_output import build_ui_service_output
from src.ui.tabs.project.pack.boot_images.view import BootImagesPack
from src.ui.tabs.project.unpack.boot_images.view import BootImagesUnpack


def _open(window_type, operation):
    window = window_type(texts=lang, on_run=lambda _mode: None)
    runner = build_ui_task_runner(
        dispatcher=build_ui_dispatcher(host_window=window),
        is_alive=window.winfo_exists,
        logger=logging,
    )
    notifier = build_ui_notifier(host_window=window)
    runtime = build_app_boot_context(output=build_ui_service_output(texts=lang, notify=notifier.show))
    controller = BootImageActionController(
        runtime=runtime,
        task_runner=runner,
        operation=lambda mode, current_runtime: operation(mode, runtime=current_runtime),
    )
    window.set_run_action(controller.run)
    return window


def open_boot_pack_window():
    return _open(BootImagesPack, run_pack)


def open_boot_unpack_window():
    return _open(BootImagesUnpack, run_unpack)


__all__ = ['open_boot_pack_window', 'open_boot_unpack_window']
