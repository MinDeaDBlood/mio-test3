from __future__ import annotations

from src.app.runtime.contexts.projects import resolve_project_manager
from src.app.runtime.contexts.settings import resolve_settings
from src.logic.common.service_output import ServiceOutput, build_service_output
from src.logic.projects.boot_images.runtime_context import (
    BootImageRuntimeContext,
    build_runtime_context as build_boot_context,
)
from src.logic.projects.common.runtime_context import (
    ProjectImportRuntimeContext,
    build_project_import_runtime_context,
)
from src.logic.projects.convert.runtime_context import (
    ConvertRuntimeContext,
    build_convert_runtime_context,
)
from src.logic.projects.dtbo.runtime_context import (
    DtboRuntimeContext,
    build_dtbo_runtime_context,
)
from src.logic.projects.logo.service import (
    LogoRuntimeContext,
    build_runtime_context as build_logo_context,
)
from src.logic.projects.pack.super.runtime_context import (
    PackSuperRuntimeContext,
    build_pack_super_runtime_context,
)
from src.logic.projects.unpack.runtime_context import (
    UnpackWorkflowRuntimeContext,
    build_workflow_runtime_context,
)


def build_app_project_import_context(
    *, output: ServiceOutput | None = None
) -> ProjectImportRuntimeContext:
    project_manager = resolve_project_manager()
    settings = resolve_settings()
    output = output or build_service_output()
    return build_project_import_runtime_context(
        project_manager=project_manager,
        auto_unpack=str(settings.auto_unpack) == "1",
        tool_bin=settings.tool_bin,
        magisk_not_decompress=settings.magisk_not_decompress,
        boot_skip_ramdisk=settings.boot_skip_ramdisk,
        output=output,
    )


def build_app_unpack_workflow_context(
    *, output: ServiceOutput | None = None
) -> UnpackWorkflowRuntimeContext:
    project_manager = resolve_project_manager()
    settings = resolve_settings()
    output = output or build_service_output()
    return build_workflow_runtime_context(
        input_path=project_manager.current_input_path(),
        work_path=project_manager.current_work_path(),
        output_path=project_manager.current_work_output_path(),
        project_selected=project_manager.exist(),
        tool_bin=settings.tool_bin,
        magisk_not_decompress=settings.magisk_not_decompress,
        boot_skip_ramdisk=settings.boot_skip_ramdisk,
        output=output,
    )


def build_app_boot_context(
    *, host_window=None, output: ServiceOutput | None = None
) -> BootImageRuntimeContext:
    output = output or build_service_output()
    project_manager = resolve_project_manager()
    settings = resolve_settings()
    input_path = project_manager.current_input_path()
    return build_boot_context(
        input_path=input_path,
        work_path=project_manager.current_work_path(),
        output_path=project_manager.current_work_output_path(),
        tool_bin=settings.tool_bin,
        magisk_not_decompress=settings.magisk_not_decompress,
        boot_skip_ramdisk=settings.boot_skip_ramdisk,
        output=output,
    )


def build_app_dtbo_context(
    *, output: ServiceOutput | None = None
) -> DtboRuntimeContext:
    project_manager = resolve_project_manager()
    return build_dtbo_runtime_context(
        work_path=project_manager.current_work_path(),
        output_path=project_manager.current_work_output_path(),
        output=output or build_service_output(),
    )


def build_app_convert_context(
    *, output: ServiceOutput | None = None
) -> ConvertRuntimeContext:
    project_manager = resolve_project_manager()
    return build_convert_runtime_context(
        # Conversion reads immutable source images from input and performs all
        # mutations in output.
        work_path=project_manager.current_input_path(),
        output_path=project_manager.current_work_output_path(),
        output=output or build_service_output(),
    )


def build_app_pack_super_context() -> PackSuperRuntimeContext:
    project_manager = resolve_project_manager()
    output_path = project_manager.current_work_output_path()
    return build_pack_super_runtime_context(
        work_path=output_path,
        output_path=output_path,
    )


def build_app_logo_context(
    *, host_window=None, output: ServiceOutput | None = None
) -> LogoRuntimeContext:
    output = output or build_service_output()
    return build_logo_context(
        work_path=resolve_project_manager().current_work_path(),
        output=output,
    )


__all__ = [
    "build_app_boot_context",
    "build_app_convert_context",
    "build_app_dtbo_context",
    "build_app_logo_context",
    "build_app_pack_super_context",
    "build_app_project_import_context",
    "build_app_unpack_workflow_context",
]
