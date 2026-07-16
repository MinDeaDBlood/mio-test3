from __future__ import annotations

import logging
import os

from src.core import mkdtboimg
from src.core.process_runner import call
from src.core.file_finder import findfile
from src.logic.common.messages import message
from src.logic.projects.common.fs_service import re_folder
from src.logic.projects.common.workspace_service import rmdir
from src.logic.projects.dtbo.runtime_context import DtboRuntimeContext, build_dtbo_runtime_context


def unpack_dtbo(
    name: str = 'dtbo',
    *,
    image_path: str | None = None,
    remove_source: bool = True,
    runtime: DtboRuntimeContext | None = None,
    findfile_func=findfile,
    dump_func=mkdtboimg.dump_dtbo,
    call_func=call,
    re_folder_func=re_folder,
    rmdir_func=rmdir,
    listdir_func=os.listdir,
    remove_func=os.remove,
    logger=None,
) -> bool:
    if runtime is None:
        raise ValueError('This operation requires an explicit runtime context.')
    logger = logger or logging
    work = runtime.work_path
    dtbo_image = image_path or findfile_func(f'{name}.img', work)
    if not dtbo_image:
        runtime.output.log(message('file_not_found', 'File not found: {item}', item=name))
        return False

    target_root = os.path.join(work, name)
    target_dtbo = os.path.join(target_root, 'dtbo')
    target_dts = os.path.join(target_root, 'dts')
    re_folder_func(target_root)
    re_folder_func(target_dtbo)
    re_folder_func(target_dts)

    try:
        dump_func(dtbo_image, os.path.join(target_dtbo, 'dtbo'))
    except (OSError, RuntimeError, ValueError) as exc:
        logger.exception('Failed to dump dtbo image')
        runtime.output.log(message('extract_failed', 'Extraction failed: {error}', error=exc))
        return False

    entries = [entry for entry in listdir_func(target_dtbo) if entry.startswith('dtbo.')]
    if not entries:
        runtime.output.log(message('extract_failed', 'Extraction failed: {error}', error='DTBO contains no entries'))
        return False
    for entry in entries:
        runtime.output.log(message('dtbo_extracting_entry', 'Extracting DTBO entry: {entry}', entry=entry))
        result = call_func(
            [
                'dtc',
                '-@',
                '-I',
                'dtb',
                '-O',
                'dts',
                os.path.join(target_dtbo, entry),
                '-o',
                os.path.join(target_dts, 'dts.' + os.path.basename(entry).rsplit('.', 1)[1]),
            ],
            out=False,
        )
        if result != 0:
            runtime.output.log(message('extract_failed', 'Extraction failed: {error}', error=entry))
            return False
    runtime.output.log(message('dtbo_unpack_complete', 'DTBO unpack completed'))
    if remove_source:
        try:
            remove_func(dtbo_image)
        except OSError:
            logger.exception('Failed to remove original dtbo image after unpack')
    rmdir_func(target_dtbo)
    return True


def pack_dtbo(
    *,
    runtime: DtboRuntimeContext | None = None,
    exists_func=os.path.exists,
    listdir_func=os.listdir,
    call_func=call,
    create_func=mkdtboimg.create_dtbo,
    re_folder_func=re_folder,
    rmdir_func=rmdir,
) -> bool:
    if runtime is None:
        raise ValueError('This operation requires an explicit runtime context.')
    work = runtime.work_path
    dtbo_root = os.path.join(work, 'dtbo')
    dts_dir = os.path.join(dtbo_root, 'dts')
    dtbo_dir = os.path.join(dtbo_root, 'dtbo')
    if not exists_func(dts_dir) or not exists_func(dtbo_root):
        runtime.output.log(message('dtbo_source_missing', 'DTBO source files are missing'))
        return False

    re_folder_func(dtbo_dir)
    for dts in listdir_func(dts_dir):
        if not dts.startswith('dts.'):
            continue
        runtime.output.log(message('dtbo_compiling', 'Compiling DTS: {path}', path=dts))
        call_func(
            [
                'dtc',
                '-@',
                '-I',
                'dts',
                '-O',
                'dtb',
                os.path.join(dts_dir, dts),
                '-o',
                os.path.join(dtbo_dir, 'dtbo.' + os.path.basename(dts).rsplit('.', 1)[1]),
            ],
            out=False,
        )

    runtime.output.log(message('dtbo_created', 'Created DTBO image: {path}', path='dtbo.img'))
    images = [
        os.path.join(dtbo_dir, filename)
        for filename in listdir_func(dtbo_dir)
        if filename.startswith('dtbo.')
    ]
    create_func(
        os.path.join(runtime.output_path, 'dtbo.img'),
        sorted(images, key=lambda item: int(item.rsplit('.', 1)[1])),
        4096,
    )
    rmdir_func(dtbo_root)
    runtime.output.log(message('operation_complete', 'Operation completed'))
    return True


build_runtime_context = build_dtbo_runtime_context

__all__ = ['DtboRuntimeContext', 'build_dtbo_runtime_context', 'build_runtime_context', 'pack_dtbo', 'unpack_dtbo']
