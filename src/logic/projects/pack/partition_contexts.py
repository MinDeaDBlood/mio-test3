from __future__ import annotations

import os
from typing import Any


def build_fs_config_path(work: str, partition_name: str) -> str:
    return os.path.normpath(os.path.join(work, "config", f"{partition_name}_fs_config"))


def build_file_contexts_path(work: str, partition_name: str) -> str:
    return os.path.normpath(
        os.path.join(work, "config", f"{partition_name}_file_contexts")
    )


def prepare_partition_context_files(
    *,
    work: str,
    partition_name: str,
    request: Any,
    parts_dict: dict,
    runtime: Any,
    deps: Any,
) -> str:
    """Prepare fs_config/file_contexts metadata before packing a filesystem partition.

    The high-level partition-flow service should only orchestrate the pack.  This
    helper owns the legacy fs_config patch, optional context-rule learning, duplicate
    cleanup and fs-conversion mutation in one narrow, UI-free boundary.
    """
    apply_requested_fs_conversion(
        partition_name=partition_name,
        parts_dict=parts_dict,
        origin_fs=request.origin_fs,
        modify_fs=request.modify_fs,
        enabled=bool(request.fs_convert),
    )

    fs_config_path = build_fs_config_path(work, partition_name)
    contexts_file = build_file_contexts_path(work, partition_name)

    if os.access(fs_config_path, os.F_OK):
        deps.fspatch_main(work + partition_name, fs_config_path)
        deps.remove_duplicate_func(fs_config_path)

    if os.path.exists(contexts_file):
        _patch_context_rules_if_enabled(
            work=work,
            partition_name=partition_name,
            contexts_file=contexts_file,
            runtime=runtime,
            deps=deps,
        )
        deps.remove_duplicate_func(contexts_file)

    return contexts_file


def _patch_context_rules_if_enabled(
    *,
    work: str,
    partition_name: str,
    contexts_file: str,
    runtime: Any,
    deps: Any,
) -> None:
    if not runtime.context_patch_enabled:
        return
    deps.contextpatch_main(
        work + partition_name, contexts_file, runtime.context_rule_file
    )
    new_rules = deps.contextpatch_scan_context(contexts_file)
    rules = deps.json_edit_cls(runtime.context_rule_file)
    rules.write(new_rules | rules.read())


def apply_requested_fs_conversion(
    *,
    partition_name: str,
    parts_dict: dict,
    origin_fs: str,
    modify_fs: str,
    enabled: bool,
) -> None:
    if enabled and parts_dict[partition_name] == origin_fs:
        parts_dict[partition_name] = modify_fs


__all__ = [
    "apply_requested_fs_conversion",
    "build_file_contexts_path",
    "build_fs_config_path",
    "prepare_partition_context_files",
]
