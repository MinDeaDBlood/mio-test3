"""Application orchestration for packaging the current project."""

from __future__ import annotations

from collections.abc import Callable

from src.app.projects.pack.hybrid_action import HybridPackAction, build_hybrid_pack_action
from src.app.runtime.contexts.projects import resolve_current_project_name, resolve_project_manager
from src.logic.common.messages import message
from src.logic.common.service_output import OutputSeverity, ServiceOutput, build_service_output
from src.logic.projects.common.workspace_service import pack_zip as pack_zip_service


HybridOptionPrompt = Callable[[object], bool | None]
TargetDevicePrompt = Callable[[object], str | None]


def pack_current_project_zip(
    *,
    host_window: object,
    prompt_hybrid_option: HybridOptionPrompt,
    prompt_target_device: TargetDevicePrompt,
    output: ServiceOutput | None = None,
    hybrid_action: HybridPackAction | None = None,
) -> bool:
    project_manager = resolve_project_manager()
    output = output or build_service_output()
    if not project_manager.exist():
        output.report(
            message('project_not_selected', 'Project is not selected'),
            severity=OutputSeverity.WARNING,
        )
        return False

    pack_hybrid = prompt_hybrid_option(host_window)
    if pack_hybrid is None:
        return False
    if pack_hybrid:
        right_device = prompt_target_device(host_window)
        if right_device is None:
            return False
        try:
            (hybrid_action or build_hybrid_pack_action(project_manager=project_manager)).execute(right_device)
        except Exception as exc:
            output.log_and_report(
                message(
                    'operation_failed',
                    'Hybrid ROM packing failed: {reason}',
                    reason=str(exc),
                ),
                severity=OutputSeverity.ERROR,
            )
            return False

    project_name = resolve_current_project_name().get()
    output_dir = project_manager.current_work_output_path()
    pack_zip_service(
        input_dir=output_dir,
        output_zip=f'{output_dir}/{project_name}.zip',
        silent=False,
        project_name=project_name,
        output=output,
    )
    return True


__all__ = ['pack_current_project_zip']
