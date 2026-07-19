from __future__ import annotations

import logging

from src.app.background_jobs import start_background_job
from src.app.projects.unpack.controller import UnpackWorkspaceController
from src.app.projects.unpack.runtime import (
    UnpackRuntimeContext,
    build_unpack_view_runtime_context,
)
from src.app.projects.unpack.view_controller import UnpackViewController
from src.app.composition.service_output import build_ui_service_output
from src.app.ui_feedback import build_ui_notifier
from src.app.localization_runtime import lang
from src.core.file_types import gettype
from src.core.byte_size import format_bytes
from src.core.json_store import JsonEdit
from src.logic.projects.unpack.workflow.service import unpack
from src.logic.projects.unpack.runtime_context import build_workflow_runtime_context
from src.logic.projects.unpack.workspace_service import UnpackWorkspaceService
from src.app.composition.partition_pack import open_partition_pack
from src.ui.tabs.project.unpack.info_dialog import show_unpack_image_info_dialog
from src.ui.tabs.project.unpack.presenter import UnpackPresenter
from src.ui.tabs.project.unpack.view import UnpackGui


def create_unpack_view(*, project_runtime):
    ui_runtime = build_unpack_view_runtime_context(
        host_window=project_runtime.host_window,
        project_manager=project_runtime.project_manager,
        current_project_name=project_runtime.current_project_name,
        start_worker=start_background_job,
    )

    def notify_on_ui_thread(**kwargs):
        return ui_runtime.dispatcher.dispatch(
            lambda: project_runtime.notifier.show(**kwargs)
        )

    workflow_output = build_ui_service_output(
        texts=lang,
        notify=notify_on_ui_thread,
    )

    def dispatch_unpack(chosen, form=""):
        # Project selection can change after the Projects tab was created.  Build
        # the workflow paths at the moment the user starts the operation instead
        # of retaining the initial (and often empty) project paths.
        manager = ui_runtime.project_manager
        settings = ui_runtime.settings
        workflow_runtime = build_workflow_runtime_context(
            input_path=manager.current_input_path(),
            work_path=manager.current_work_path(),
            output_path=manager.current_work_output_path(),
            project_selected=manager.exist(),
            tool_bin=settings.tool_bin,
            magisk_not_decompress=settings.magisk_not_decompress,
            boot_skip_ramdisk=settings.boot_skip_ramdisk,
            output=workflow_output,
        )
        return unpack(chosen, form, runtime=workflow_runtime)

    def open_pack_partitions(selected):
        return open_partition_pack(selected)

    runtime = UnpackRuntimeContext(
        current_project_name=ui_runtime.current_project_name,
        project_manager=ui_runtime.project_manager,
        json_edit_cls=JsonEdit,
        format_bytes_func=format_bytes,
        gettype_func=gettype,
        unpack_func=dispatch_unpack,
        notifier=build_ui_notifier(
            ui_runtime.message_pop, host_window=ui_runtime.host_window
        ),
        animation=ui_runtime.animation,
        open_pack_partitions=open_pack_partitions,
        dispatcher=ui_runtime.dispatcher,
    )
    workspace_service = UnpackWorkspaceService(
        json_edit_cls=runtime.json_edit_cls,
        gettype_func=runtime.gettype_func,
    )
    workspace_controller = UnpackWorkspaceController(
        project_manager=runtime.project_manager,
        workspace_service=workspace_service,
        unpack_func=runtime.unpack_func,
        logger=logging,
    )
    presenter = UnpackPresenter(texts=lang)
    view = UnpackGui(
        master=ui_runtime.host_window.tab2,
        current_project_name=ui_runtime.current_project_name,
        texts=lang,
    )
    view_controller = UnpackViewController(
        view,
        runtime=runtime,
        controller=workspace_controller,
        presenter=presenter,
        task_runner=ui_runtime.task_runner,
        show_info_dialog=lambda **kwargs: show_unpack_image_info_dialog(
            texts=lang, **kwargs
        ),
        texts=lang,
        logger=logging,
    )
    view.attach_controller(view_controller)
    return view


__all__ = ["create_unpack_view"]
