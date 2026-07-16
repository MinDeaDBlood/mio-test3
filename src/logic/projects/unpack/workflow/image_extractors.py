from __future__ import annotations

import logging
import os
import struct

from src.core import ext4, imgextractor
from src.core.imgkit import unpack_image as imgkit_unpack_image
from src.core.process_runner import call
from src.core.splash_editor import process_splashimg
from src.logic.common.messages import message
from src.logic.projects.unpack.gpt import extract_gpt_partitions
from src.logic.projects.unpack.runtime_context import UnpackWorkflowRuntimeContext
from src.logic.projects.unpack.workflow.image_adapters import runtime_output
from src.logic.projects.unpack.workflow.source_handlers import metadata_file_valid


def partition_metadata_valid(work: str, partition_name: str) -> bool:
    config_dir = os.path.join(work, 'config')
    return all(
        metadata_file_valid(os.path.join(config_dir, f'{partition_name}_{suffix}'))
        for suffix in ('fs_config', 'file_contexts')
    )


def is_path_inside(child_path: str, parent_path: str) -> bool:
    try:
        return os.path.commonpath([os.path.abspath(child_path), os.path.abspath(parent_path)]) == os.path.abspath(parent_path)
    except ValueError:
        return False


def remove_work_image_after_success(image_path: str, work: str, *, output) -> bool:
    if not is_path_inside(image_path, work):
        return True
    try:
        os.remove(image_path)
    except FileNotFoundError:
        return True
    except OSError as exc:
        output.report(
            message('operation_failed', 'Operation failed: {item}', item=f'{os.path.basename(image_path)}: {exc}')
        )
        return False
    return True


def extract_ext_image(
    runtime: UnpackWorkflowRuntimeContext,
    work: str,
    partition_name: str,
    parts: dict,
    *,
    image_path: str | None = None,
) -> bool:
    output = runtime_output(runtime)
    image_path = image_path or os.path.join(work, f'{partition_name}.img')
    target_path = os.path.join(work, partition_name)
    try:
        with open(image_path, 'rb+') as stream:
            mount = ext4.Volume(stream).get_mount_point
            if mount[:1] == '/':
                mount = mount[1:]
            if '/' in mount:
                mount = mount.split('/')[-1]
            if mount != partition_name and mount and partition_name != 'mi_ext':
                parts[mount] = 'ext'
        imgextractor.Extractor().main(image_path, target_path, work)
    except (OSError, RuntimeError, ValueError, EOFError, struct.error):
        logging.exception('unpack.workflow.ext_extract_failed: partition=%s; image_path=%s', partition_name, image_path)
        output.report(message('operation_failed', 'Operation failed: {item}', item=f'{partition_name}.img'))
        return False
    if not os.path.isdir(target_path) or not partition_metadata_valid(work, partition_name):
        output.report(message('operation_failed', 'Operation failed: {item}', item=f'{partition_name}.img metadata'))
        return False
    return remove_work_image_after_success(image_path, work, output=output)


def extract_erofs_image(
    runtime: UnpackWorkflowRuntimeContext,
    work: str,
    partition_name: str,
    *,
    image_path: str | None = None,
) -> bool:
    output = runtime_output(runtime)
    image_path = image_path or os.path.join(work, f'{partition_name}.img')
    target_path = os.path.join(work, partition_name)
    if call(exe=['extract.erofs', '-i', image_path, '-o', work, '-x'], out=False) != 0:
        output.log('Unpack failed...')
        return False
    if not os.path.isdir(target_path) or not partition_metadata_valid(work, partition_name):
        output.report(message('operation_failed', 'Operation failed: {item}', item=f'{partition_name}.img metadata'))
        return False
    return remove_work_image_after_success(image_path, work, output=output)


def extract_f2fs_image(
    runtime: UnpackWorkflowRuntimeContext,
    work: str,
    partition_name: str,
    *,
    image_path: str | None = None,
) -> bool:
    output = runtime_output(runtime)
    image_path = image_path or os.path.join(work, f'{partition_name}.img')
    target_path = os.path.join(work, partition_name)
    config_dir = os.path.join(work, 'config')
    os.makedirs(config_dir, exist_ok=True)
    try:
        imgkit_unpack_image(
            image_path,
            work,
            fs_config_path=os.path.join(config_dir, f'{partition_name}_fs_config'),
            file_contexts_path=os.path.join(config_dir, f'{partition_name}_file_contexts'),
        )
    except (OSError, RuntimeError, ValueError):
        logging.exception('unpack.workflow.f2fs_imgkit_failed: partition=%s; image_path=%s', partition_name, image_path)
        output.report(message('operation_failed', 'Operation failed: {item}', item=f'{partition_name}.img'))
        return False
    if not os.path.isdir(target_path) or not partition_metadata_valid(work, partition_name):
        output.report(message('operation_failed', 'Operation failed: {item}', item=f'{partition_name}.img metadata'))
        return False
    return remove_work_image_after_success(image_path, work, output=output)


def extract_splash_image(
    runtime: UnpackWorkflowRuntimeContext,
    work: str,
    partition_name: str,
    *,
    image_path: str | None = None,
) -> bool:
    output = runtime_output(runtime)
    image_path = image_path or os.path.join(work, f'{partition_name}.img')
    target_path = os.path.join(work, partition_name)
    try:
        paths = process_splashimg(image_path, os.path.join(target_path, 'splash.png'))
    except (OSError, RuntimeError, ValueError, EOFError, struct.error):
        logging.exception('unpack.workflow.splash_extract_failed: partition=%s; image_path=%s', partition_name, image_path)
        output.report(message('operation_failed', 'Operation failed: {item}', item=f'{partition_name}.img'))
        return False
    return bool(paths) and all(path.is_file() and path.stat().st_size > 0 for path in paths)


def extract_gpt_image(
    runtime: UnpackWorkflowRuntimeContext,
    work: str,
    partition_name: str,
    *,
    image_path: str | None = None,
) -> bool:
    output = runtime_output(runtime)
    image_path = image_path or os.path.join(work, f'{partition_name}.img')
    try:
        result = extract_gpt_partitions(image_path, work)
    except (OSError, RuntimeError, ValueError, EOFError, struct.error):
        logging.exception('unpack.workflow.gpt_extract_failed: partition=%s; image_path=%s', partition_name, image_path)
        output.report(message('operation_failed', 'Operation failed: {item}', item=f'{partition_name}.img'))
        return False
    return bool(result.partitions) and all(
        item.output_path.is_file() and item.output_path.stat().st_size > 0
        for item in result.partitions
    )


__all__ = [
    'extract_erofs_image',
    'extract_ext_image',
    'extract_f2fs_image',
    'extract_gpt_image',
    'extract_splash_image',
]
