from __future__ import annotations

from src.logic.projects.unpack.runtime_context import UnpackWorkflowRuntimeContext


def unpack_dtbo(
    name: str = "dtbo", *, image_path: str | None = None, workflow_runtime=None
):
    from src.logic.projects.dtbo.runtime_context import build_dtbo_runtime_context
    from src.logic.projects.dtbo.service import unpack_dtbo as unpack_dtbo_service

    runtime = None
    if workflow_runtime is not None:
        runtime = build_dtbo_runtime_context(
            work_path=workflow_runtime.work_path,
            output_path=workflow_runtime.output_path,
            output=runtime_output(workflow_runtime),
        )
    return unpack_dtbo_service(
        name, image_path=image_path, remove_source=False, runtime=runtime
    )


def dump_logo(
    file_path: str,
    output: str | None = None,
    output_name: str = "logo",
    *,
    work_path: str | None = None,
    service_output=None,
):
    from src.logic.projects.logo.service import (
        LogoRuntimeContext,
        dump_logo as dump_logo_service,
    )

    runtime = None
    if service_output is not None and work_path is not None:
        runtime = LogoRuntimeContext(work_path=work_path, output=service_output)
    return dump_logo_service(file_path, output, output_name, runtime=runtime)


def unpack_boot(
    name: str = "boot", *, image_path: str | None = None, workflow_runtime=None
):
    from src.logic.projects.boot_images.runtime_context import (
        build_runtime_context as build_boot_runtime_context,
    )
    from src.logic.projects.unpack.boot_images.service import (
        unpack_boot as unpack_boot_service,
    )

    runtime = None
    if workflow_runtime is not None:
        runtime = build_boot_runtime_context(
            input_path=workflow_runtime.input_path,
            work_path=workflow_runtime.work_path,
            output_path=workflow_runtime.output_path,
            tool_bin=workflow_runtime.tool_bin,
            magisk_not_decompress=workflow_runtime.magisk_not_decompress,
            boot_skip_ramdisk=workflow_runtime.boot_skip_ramdisk,
            output=runtime_output(workflow_runtime),
        )
    work = workflow_runtime.work_path if workflow_runtime is not None else None
    return unpack_boot_service(name, boot=image_path, work=work, runtime=runtime)


def runtime_output(runtime: UnpackWorkflowRuntimeContext) -> object:
    if runtime is None or runtime.output is None:
        raise ValueError("Unpack workflow requires an output port.")
    return runtime.output


__all__ = ["dump_logo", "runtime_output", "unpack_boot", "unpack_dtbo"]
