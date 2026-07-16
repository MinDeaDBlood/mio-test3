from __future__ import annotations

import logging

from src.app.localization_runtime import lang
from src.app.background_jobs import start_background_job
from src.app.project_pack import pack_current_project_zip
from src.app.projects.runtime import build_project_workspace_runtime_context
from src.platform.system_shell import open_in_file_manager
from src.app.window_launchers import open_pack_super_window
from src.logic.projects.project_menu.controller import ProjectMenuController
from src.ui.common.controls import input_
from src.app.composition.service_output import build_ui_service_output
from src.ui.tabs.project.action_panel_widget import ProjectActionPanelWidget
from src.ui.tabs.project.pack.hybrid.device_prompt import prompt_target_device
from src.ui.tabs.project.pack.zip_prompt import prompt_hybrid_pack_option
from src.ui.tabs.project.project_menu_widget import ProjectMenuWidget
from src.app.composition.unpack import create_unpack_view


def create_project_workspace(*, host_window):
    runtime = build_project_workspace_runtime_context(
        host_window=host_window,
        start_worker=start_background_job,
    )
    controller = ProjectMenuController(
        project_manager=runtime.project_manager,
        current_project_getter=runtime.current_project_name.get,
        current_project_setter=runtime.current_project_name.set,
    )
    project_menu = ProjectMenuWidget(
        master=runtime.host_window.tab2,
        texts=lang,
        current_project_name=runtime.current_project_name,
        controller=controller,
        input_func=input_,
        open_directory=open_in_file_manager,
        show_message=runtime.notifier.show,
        emit=logging.info,
    )
    unpack_view = create_unpack_view(project_runtime=runtime)

    def pack_zip():
        return pack_current_project_zip(
            host_window=runtime.host_window,
            prompt_hybrid_option=lambda host: prompt_hybrid_pack_option(host, texts=lang),
            prompt_target_device=lambda host: prompt_target_device(host, texts=lang),
            output=build_ui_service_output(texts=lang, notify=runtime.notifier.show),
        )

    def open_convert():
        from src.app.composition.convert import open_conversion_window
        return open_conversion_window(master=runtime.host_window)

    action_panel = ProjectActionPanelWidget(
        master=runtime.host_window.tab2,
        texts=lang,
        pack_zip=pack_zip,
        pack_super=open_pack_super_window,
        open_notepad=lambda: runtime.host_window.notepad.select(runtime.host_window.tab7),
        open_convert=open_convert,
        run_background=runtime.task_runner.fire_and_forget,
    )
    return {
        'runtime': runtime,
        'project_menu': project_menu,
        'unpack_view': unpack_view,
        'action_panel': action_panel,
    }


__all__ = ['create_project_workspace']
