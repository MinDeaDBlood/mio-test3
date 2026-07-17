"""Application orchestration for packaging the current project."""

from __future__ import annotations

from collections.abc import Callable
import logging

from src.app.projects.pack.hybrid_action import HybridPackAction, build_hybrid_pack_action
from src.app.runtime.contexts.projects import resolve_current_project_name, resolve_project_manager
from src.logic.common.messages import message
from src.logic.common.service_output import OutputSeverity, ServiceOutput, build_service_output
from src.logic.projects.common.workspace_service import pack_zip as pack_zip_service
from src.platform.operation_logging import operation_context


HybridOptionPrompt = Callable[[object], bool | None]
TargetDevicePrompt = Callable[[object], str | None]

logger = logging.getLogger(__name__)


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
        logger.warning("project_zip.rejected: reason=project_not_selected")
        output.report(
            message('project_not_selected', 'Project is not selected'),
            severity=OutputSeverity.WARNING,
        )
        return False

    project_name = str(resolve_current_project_name().get())
    output_dir = project_manager.current_work_output_path()
    output_zip = f'{output_dir}/{project_name}.zip'
    with operation_context(
        "project.pack_zip",
        project_name=project_name,
        output_dir=output_dir,
        output_zip=output_zip,
    ):
        logger.info("project_zip.options_requested: project=%s", project_name)
        pack_hybrid = prompt_hybrid_option(host_window)
        if pack_hybrid is None:
            logger.info("project_zip.cancelled: stage=options project=%s", project_name)
            return False
        logger.info(
            "project_zip.options_selected: project=%s hybrid=%s",
            project_name,
            pack_hybrid,
        )
        if pack_hybrid:
            right_device = prompt_target_device(host_window)
            if right_device is None:
                logger.info(
                    "project_zip.cancelled: stage=target_device project=%s",
                    project_name,
                )
                return False
            logger.info(
                "project_zip.hybrid_started: project=%s target_device=%s",
                project_name,
                right_device,
            )
            try:
                (hybrid_action or build_hybrid_pack_action(
                    project_manager=project_manager
                )).execute(right_device)
            except Exception as exc:
                logger.exception(
                    "project_zip.hybrid_failed: project=%s target_device=%s",
                    project_name,
                    right_device,
                )
                output.log_and_report(
                    message(
                        'operation_failed',
                        'Hybrid ROM packing failed: {reason}',
                        reason=str(exc),
                    ),
                    severity=OutputSeverity.ERROR,
                )
                return False
            logger.info(
                "project_zip.hybrid_completed: project=%s target_device=%s",
                project_name,
                right_device,
            )

        logger.info(
            "project_zip.archive_started: input_dir=%s output_zip=%s",
            output_dir,
            output_zip,
        )
        pack_zip_service(
            input_dir=output_dir,
            output_zip=output_zip,
            silent=False,
            project_name=project_name,
            output=output,
        )
        logger.info("project_zip.archive_completed: output_zip=%s", output_zip)
        return True


__all__ = ['pack_current_project_zip']
