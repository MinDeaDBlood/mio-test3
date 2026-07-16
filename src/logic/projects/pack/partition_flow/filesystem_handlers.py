from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Protocol

from src.logic.common.messages import message
from src.logic.common.service_output import OutputSeverity
from src.logic.projects.pack.partition_contexts import prepare_partition_context_files
from src.logic.projects.pack.partition_output import finalize_partition_output
from src.logic.projects.pack.partition_size import (
    check_ext4_size_fit,
    resolve_configured_ext4_size,
)

from .models import PackPartitionRequest

PACKABLE_FILESYSTEM_TYPES: frozenset[str] = frozenset({"ext", "erofs", "f2fs"})


@dataclass(frozen=True)
class PackFilesystemContext:
    work: str
    partition_name: str
    request: PackPartitionRequest
    parts_dict: dict
    runtime: Any
    deps: Any
    contexts_file: str


class FilesystemPackHandler(Protocol):
    fs_type: str

    def pack(self, context: PackFilesystemContext) -> int | None: ...


class ErofsPackHandler:
    fs_type = "erofs"

    def pack(self, context: PackFilesystemContext) -> int | None:
        request = context.request
        return context.deps.mkerofs_func(
            context.partition_name,
            str(request.erofs_compress_format),
            work=context.work,
            work_output=context.runtime.output_path,
            level=int(request.erofs_level),
            old_kernel=request.erofs_old_kernel,
            UTC=request.utc,
            output=context.runtime.output,
        )


class F2fsPackHandler:
    fs_type = "f2fs"

    def pack(self, context: PackFilesystemContext) -> int | None:
        return context.deps.make_f2fs_func(
            context.partition_name,
            work=context.work,
            work_output=context.runtime.output_path,
            UTC=context.request.utc,
            output=context.runtime.output,
        )


class Ext4PackHandler:
    fs_type = "ext"

    def pack(self, context: PackFilesystemContext) -> int | None:
        request = context.request
        ext4_size_value = resolve_configured_ext4_size(
            context.work,
            context.partition_name,
            request.custom_size.get(context.partition_name, 0),
        )
        size_fit = check_ext4_size_fit(
            os.path.join(context.work, context.partition_name), ext4_size_value
        )
        if ext4_size_value and not size_fit.fits:
            context.runtime.output.log(
                message(
                    "ext4_size_too_small",
                    "{partition}: selected EXT4 size {requested} bytes may be too small; "
                    "estimated/recommended size is {recommended} bytes "
                    "(missing about {missing} bytes). "
                    "Use Auto size or set a larger custom size if the partition content changed.",
                    partition=context.partition_name,
                    requested=size_fit.requested_size,
                    recommended=size_fit.recommended_size,
                    missing=size_fit.missing_bytes,
                ),
                severity=OutputSeverity.WARNING,
            )
        if request.ext4_packer == "make_ext4fs":
            result = context.deps.make_ext4fs_func(
                name=context.partition_name,
                work=context.work,
                work_output=context.runtime.output_path,
                sparse=False,
                size=ext4_size_value,
                UTC=request.utc,
                has_contexts=_path_exists(context.contexts_file),
                output=context.runtime.output,
            )
        else:
            result = context.deps.mke2fs_func(
                name=context.partition_name,
                work=context.work,
                work_output=context.runtime.output_path,
                sparse=False,
                size=ext4_size_value,
                UTC=request.utc,
                output=context.runtime.output,
            )
        if result and ext4_size_value and not size_fit.fits:
            context.runtime.output.log(
                message(
                    "ext4_fixed_size_build_failed",
                    "{partition}: build failed with fixed EXT4 size {requested} bytes. "
                    "The unpacked folder likely no longer fits the original image size; "
                    "estimated/recommended size is {recommended} bytes. "
                    "Switch Size to Auto or increase the custom size.",
                    partition=context.partition_name,
                    requested=size_fit.requested_size,
                    recommended=size_fit.recommended_size,
                ),
                severity=OutputSeverity.ERROR,
            )
        return result


class PackFilesystemHandlerRegistry:
    def __init__(self, handlers: tuple[FilesystemPackHandler, ...] | None = None):
        handlers = handlers or (
            ErofsPackHandler(),
            F2fsPackHandler(),
            Ext4PackHandler(),
        )
        self._handlers = {handler.fs_type: handler for handler in handlers}

    def is_supported(self, fs_type: str) -> bool:
        return fs_type in self._handlers

    def pack(self, context: PackFilesystemContext) -> int | None:
        handler = self._handlers.get(context.parts_dict[context.partition_name])
        if handler is None:
            raise ValueError(
                f"Unsupported filesystem pack type: {context.parts_dict[context.partition_name]}"
            )
        return handler.pack(context)


def pack_filesystem_partition(
    *,
    work: str,
    partition_name: str,
    request: PackPartitionRequest,
    parts_dict: dict,
    runtime: Any,
    deps: Any,
    registry: PackFilesystemHandlerRegistry | None = None,
) -> bool:
    contexts_file = prepare_partition_context_files(
        work=work,
        partition_name=partition_name,
        request=request,
        parts_dict=parts_dict,
        runtime=runtime,
        deps=deps,
    )
    context = PackFilesystemContext(
        work=work,
        partition_name=partition_name,
        request=request,
        parts_dict=parts_dict,
        runtime=runtime,
        deps=deps,
        contexts_file=contexts_file,
    )
    exit_code = (registry or PackFilesystemHandlerRegistry()).pack(context)
    if exit_code:
        runtime.output.log(
            message(
                "operation_failed", "Operation failed: {item}", item=partition_name
            ),
            severity=OutputSeverity.ERROR,
        )
        return False
    finalized = finalize_partition_output(
        output_format=request.output_format,
        output_dir=runtime.output_path,
        partition_name=partition_name,
        brotli_level=request.brotli_level,
        dat_version=parts_dict.get("dat_ver", 4),
        apply_output_format_func=deps.apply_output_format_func,
        output=runtime.output,
    )
    if not finalized:
        runtime.output.log(
            message(
                "operation_failed", "Operation failed: {item}", item=partition_name
            ),
            severity=OutputSeverity.ERROR,
        )
        return False
    if request.remove_source_files:
        if not deps.rdi_func(work, partition_name, output=runtime.output):
            return False
    return True


def _path_exists(path: str) -> bool:
    # Small wrapper keeps the Ext4 handler easy to unit-test while preserving
    # the legacy behavior of checking whether file_contexts were generated.
    import os

    return os.path.exists(path)


__all__ = [
    "PACKABLE_FILESYSTEM_TYPES",
    "Ext4PackHandler",
    "F2fsPackHandler",
    "ErofsPackHandler",
    "FilesystemPackHandler",
    "PackFilesystemContext",
    "PackFilesystemHandlerRegistry",
    "pack_filesystem_partition",
]
