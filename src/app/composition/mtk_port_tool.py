from __future__ import annotations

from src.app.localization_runtime import lang
import logging

from src.app.tools.mtk_port_controller import MtkPortController
from src.app.tools.mtk_port_profiles import load_or_create_mtk_port_profiles
from src.app.tools.mtk_port_sources import detect_mtk_port_source_defaults
from src.app.runtime.contexts.ui import resolve_ui_host_window
from src.app.ui_feedback import build_ui_dispatcher
from src.app.ui_tasks import build_ui_task_runner
from src.platform.runtime_paths import MTK_PORT_TEMP_DIR, UPDATE_BINARY_FILE
from src.core.paths import prog_path, tool_bin
from src.logic.tools.mtk_port_tool import MtkPortBinaries, MtkPortService
from src.app.composition.service_output import build_ui_service_output
from src.ui.tabs.tools.mtk_port_tool.window import MtkPortTool


def open_mtk_port_tool_window() -> MtkPortTool:
    defaults = detect_mtk_port_source_defaults()
    host_window = resolve_ui_host_window()
    window_ref: list[MtkPortTool] = []
    dispatcher = build_ui_dispatcher(host_window=host_window)
    task_runner = build_ui_task_runner(
        dispatcher=dispatcher,
        is_alive=lambda: bool(window_ref and window_ref[0].winfo_exists()),
        logger=logging,
    )
    controller = MtkPortController(
        service=MtkPortService(
            binaries=MtkPortBinaries.from_tool_bin(tool_bin),
            update_binary_path=UPDATE_BINARY_FILE,
            local_runtime_dir=MTK_PORT_TEMP_DIR,
            profiles=load_or_create_mtk_port_profiles(),
            output=build_ui_service_output(texts=lang),
        ),
        task_runner=task_runner,
    )
    window = MtkPortTool(
        texts=lang,
        controller=controller,
        initial_directory=prog_path,
        default_boot_image=defaults.boot_image,
        default_system_image=defaults.system_image,
    )
    window_ref.append(window)
    return window


__all__ = ["open_mtk_port_tool_window"]
