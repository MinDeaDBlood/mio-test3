from __future__ import annotations

import logging
import os

from src.core.json_store import JsonEdit
from src.core.ota_dat import Sdat2img
from src.core.process_runner import call
from src.logic.common.messages import message
from src.logic.common.service_output import OutputSeverity
from src.logic.projects.unpack.runtime_context import UnpackWorkflowRuntimeContext
from src.logic.projects.unpack.workflow.compressed_dat import unpack_compressed_dat as _unpack_compressed_dat
from src.logic.projects.unpack.workflow.image_operations import (
    process_partition_image,
    resolve_image_for_processing,
    runtime_output,
)
from src.logic.projects.unpack.workflow.platform_support import log_case_sensitive_enable_failure
from src.logic.projects.unpack.workflow.source_handlers import (
    extract_payload_images,
    extract_super_images,
    extract_update_app_images,
)


def _parts_info_editor(work: str) -> JsonEdit:
    return JsonEdit(os.path.join(work, 'config', 'parts_info'))


def _ensure_config_dir(work: str) -> None:
    os.makedirs(os.path.join(work, 'config'), exist_ok=True)


def unpack_compressed_dat(source: str, work: str, partition_name: str, parts: dict, *, output=None):
    return _unpack_compressed_dat(
        source,
        work,
        partition_name,
        parts,
        output=output,
        call_func=call,
        sdat2img_cls=Sdat2img,
    )


def process_existing_image(
    runtime: UnpackWorkflowRuntimeContext,
    work: str,
    partition_name: str,
    image_path: str,
    parts: dict,
    json_edit: JsonEdit,
) -> bool:
    return process_partition_image(runtime, work, partition_name, image_path, parts, json_edit)


def _prepare_windows_workspace(runtime: UnpackWorkflowRuntimeContext) -> None:
    if os.name != 'nt':
        return
    from ctypes import windll
    from src.core.pycase import ensure_dir_case_sensitive

    if not windll.shell32.IsUserAnAdmin():
        return
    try:
        ensure_dir_case_sensitive(runtime.work_path)
    except OSError as exc:
        log_case_sensitive_enable_failure(exc, runtime.work_path)
    except (AttributeError, RuntimeError, ValueError):
        logging.exception('unpack.workflow.enable_case_sensitive_unexpected_failed: work_path=%s', runtime.work_path)


def unpack(chose: list | dict, form: str = '', *, runtime: UnpackWorkflowRuntimeContext | None = None) -> bool:
    if runtime is None:
        raise ValueError('Unpack workflow requires an explicit UnpackWorkflowRuntimeContext.')
    output = runtime_output(runtime)
    _prepare_windows_workspace(runtime)
    if not runtime.project_exists():
        output.report(message('project_not_selected', 'Project is not selected'))
        return False
    if not os.path.exists(runtime.work_path):
        output.report(message('project_not_selected', 'Project is not selected'), severity=OutputSeverity.ERROR)
        return False
    if not chose:
        return False

    work = runtime.work_path
    source = runtime.input_path
    json_edit = _parts_info_editor(work)
    parts = json_edit.read()

    if form == 'payload':
        return extract_payload_images(source, chose, output=output)
    if form == 'super':
        return extract_super_images(source, chose, parts, json_edit, output=output)
    if form == 'update.app':
        return extract_update_app_images(source, chose)

    operation_ok = True
    processed_any = False
    for partition_name in chose:
        unpack_compressed_dat(source, work, partition_name, parts, output=output)
        image_path = resolve_image_for_processing(source, work, partition_name)
        if image_path is None:
            output.report(message('file_not_found', 'File not found: {item}', item=f'{partition_name}.img'))
            operation_ok = False
            continue
        processed_any = True
        if not process_existing_image(runtime, work, partition_name, image_path, parts, json_edit):
            operation_ok = False

    _ensure_config_dir(work)
    json_edit.write(parts)
    parts.clear()
    if operation_ok and processed_any:
        output.log(message('operation_complete', 'Operation completed'))
        return True
    output.report(message('operation_failed', 'Operation failed'))
    return False


__all__ = ['process_existing_image', 'unpack', 'unpack_compressed_dat']
