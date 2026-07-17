from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


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
    """Prepare fs_config and file_contexts metadata before packing."""
    original_type = parts_dict.get(partition_name, "unknown")
    apply_requested_fs_conversion(
        partition_name=partition_name,
        parts_dict=parts_dict,
        origin_fs=request.origin_fs,
        modify_fs=request.modify_fs,
        enabled=bool(request.fs_convert),
    )
    resolved_type = parts_dict.get(partition_name, original_type)

    fs_config_path = build_fs_config_path(work, partition_name)
    contexts_file = build_file_contexts_path(work, partition_name)
    logger.info(
        "partition_pack.metadata_prepare: partition=%s original_fs=%s resolved_fs=%s "
        "fs_config=%s fs_config_exists=%s file_contexts=%s file_contexts_exists=%s "
        "context_patch_enabled=%s",
        partition_name,
        original_type,
        resolved_type,
        fs_config_path,
        os.path.exists(fs_config_path),
        contexts_file,
        os.path.exists(contexts_file),
        runtime.context_patch_enabled,
    )

    if os.access(fs_config_path, os.F_OK):
        logger.debug(
            "partition_pack.fs_config_patch_started: partition=%s path=%s",
            partition_name,
            fs_config_path,
        )
        deps.fspatch_main(work + partition_name, fs_config_path)
        deps.remove_duplicate_func(fs_config_path)
        logger.debug(
            "partition_pack.fs_config_patch_completed: partition=%s path=%s",
            partition_name,
            fs_config_path,
        )
    else:
        logger.warning(
            "partition_pack.fs_config_missing: partition=%s path=%s",
            partition_name,
            fs_config_path,
        )

    if os.path.exists(contexts_file):
        _patch_context_rules_if_enabled(
            work=work,
            partition_name=partition_name,
            contexts_file=contexts_file,
            runtime=runtime,
            deps=deps,
        )
        deps.remove_duplicate_func(contexts_file)
        logger.debug(
            "partition_pack.file_contexts_deduplicated: partition=%s path=%s",
            partition_name,
            contexts_file,
        )
    else:
        logger.warning(
            "partition_pack.file_contexts_missing: partition=%s path=%s",
            partition_name,
            contexts_file,
        )

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
        logger.debug(
            "partition_pack.context_rules_skipped: partition=%s reason=disabled",
            partition_name,
        )
        return
    logger.info(
        "partition_pack.context_rules_started: partition=%s contexts=%s rules=%s",
        partition_name,
        contexts_file,
        runtime.context_rule_file,
    )
    deps.contextpatch_main(
        work + partition_name, contexts_file, runtime.context_rule_file
    )
    new_rules = deps.contextpatch_scan_context(contexts_file)
    rules = deps.json_edit_cls(runtime.context_rule_file)
    rules.write(new_rules | rules.read())
    logger.info(
        "partition_pack.context_rules_completed: partition=%s learned_rules=%s",
        partition_name,
        len(new_rules),
    )


def apply_requested_fs_conversion(
    *,
    partition_name: str,
    parts_dict: dict,
    origin_fs: str,
    modify_fs: str,
    enabled: bool,
) -> None:
    current_fs = parts_dict[partition_name]
    if enabled and current_fs == origin_fs:
        parts_dict[partition_name] = modify_fs
        logger.info(
            "partition_pack.fs_conversion_selected: partition=%s from=%s to=%s",
            partition_name,
            origin_fs,
            modify_fs,
        )
        return
    logger.debug(
        "partition_pack.fs_conversion_skipped: partition=%s enabled=%s "
        "detected=%s requested_origin=%s requested_target=%s",
        partition_name,
        enabled,
        current_fs,
        origin_fs,
        modify_fs,
    )


__all__ = [
    "apply_requested_fs_conversion",
    "build_file_contexts_path",
    "build_fs_config_path",
    "prepare_partition_context_files",
]
