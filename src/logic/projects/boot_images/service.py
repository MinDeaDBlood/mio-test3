from __future__ import annotations

import logging
import os
import shlex
from contextlib import contextmanager
from shutil import rmtree

from src.core.rsceutil import repack as rsceutil_repack
from src.core.rsceutil import unpack as rsceutil_unpack
from src.core.process_runner import call
from src.core.file_finder import findfile
from src.core.file_types import gettype
from src.logic.common.messages import message
from src.logic.projects.common.fs_service import re_folder
from src.logic.projects.common.workspace_service import rmdir

from .runtime_context import BootImageRuntimeContext, build_runtime_context


@contextmanager
def _working_directory(path: str):
    previous = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def unpack_boot_image(
    name: str = 'boot',
    *,
    boot: str | None = None,
    work: str | None = None,
    runtime: BootImageRuntimeContext | None = None,
    call_func=call,
    findfile_func=findfile,
    gettype_func=gettype,
    re_folder_func=re_folder,
    rmdir_func=rmdir,
    rsce_unpack_func=rsceutil_unpack,
    remove_tree_func=rmtree,
    exists_func=os.path.exists,
    access_func=os.access,
    rename_func=os.rename,
    mkdir_func=os.mkdir,
    logger=None,
):
    if runtime is None:
        raise ValueError('This operation requires an explicit runtime context.')
    logger = logger or logging
    work = work or runtime.work_path
    input_path = runtime.input_path
    boot = boot or findfile_func(f'{name}.img', input_path)
    if not boot:
        runtime.output.log(message('file_not_found', 'File not found: {item}', item=f'{name}.img'))
        return None
    if not exists_func(boot):
        runtime.output.report(message('file_not_found', 'File not found: {item}', item=name))
        return None

    target_dir = os.path.join(work, name)
    if exists_func(target_dir):
        if rmdir_func(target_dir) != 0:
            runtime.output.log(message('boot_image_unpacked', 'Boot image unpacked'))
            return None
    re_folder_func(target_dir)

    try:
        with _working_directory(target_dir):
            command = ['magiskboot', 'unpack', '-h']
            if runtime.magisk_not_decompress == '1':
                command.append('-n')
            command.append(boot)
            if call_func(command) != 0:
                runtime.output.log(f'Unpack {boot} Fail...')
                remove_tree_func(target_dir, ignore_errors=True)
                return None

            second_path = os.path.join(target_dir, 'second')
            if access_func(second_path, os.F_OK) and gettype_func(second_path) == 'rk_rsce':
                runtime.output.log('Unpack Rk resource...')
                rsce_unpack_func(second_path, os.path.join(target_dir, 'second_dump'), os.path.join(target_dir, 'second_order'))
                runtime.output.log('Unpack Rk resource successfully...')

            ramdisk_cpio = os.path.join(target_dir, 'ramdisk.cpio')
            if access_func(ramdisk_cpio, os.F_OK) and runtime.boot_skip_ramdisk == '0':
                comp = gettype_func(ramdisk_cpio)
                runtime.output.log(f'Ramdisk is {comp}')
                with open(os.path.join(target_dir, 'comp'), 'w', encoding='utf-8') as handle:
                    handle.write(comp)
                if comp != 'unknown':
                    rename_func(ramdisk_cpio, os.path.join(target_dir, 'ramdisk.cpio.comp'))
                    if call_func(['magiskboot', 'decompress', os.path.join(target_dir, 'ramdisk.cpio.comp'), ramdisk_cpio]) != 0:
                        runtime.output.log('Failed to decompress Ramdisk...')
                        return None
                ramdisk_dir = os.path.join(target_dir, 'ramdisk')
                if not exists_func(ramdisk_dir):
                    mkdir_func(ramdisk_dir)
                runtime.output.log('Unpacking Ramdisk...')
                if call_func(['cpio', '-i', '-d', '-F', 'ramdisk.cpio', '-D', 'ramdisk']) != 0:
                    runtime.output.log('Failed to unpack Ramdisk...')
                    remove_tree_func(target_dir, ignore_errors=True)
                    return None
    except (OSError, RuntimeError, ValueError):
        logger.exception('Boot image unpack failed')
        raise

    runtime.output.log(message('boot_image_unpack_done', 'Unpack {name}.img done.', name=name))
    return True


def repack_boot_image(
    name: str = 'boot',
    *,
    source: str | None = None,
    boot: str | None = None,
    runtime: BootImageRuntimeContext | None = None,
    call_func=call,
    findfile_func=findfile,
    rsce_repack_func=rsceutil_repack,
    exists_func=os.path.exists,
    isdir_func=os.path.isdir,
    isfile_func=os.path.isfile,
    remove_func=os.remove,
    rename_func=os.rename,
    rmdir_func=rmdir,
    logger=None,
):
    if runtime is None:
        raise ValueError('This operation requires an explicit runtime context.')
    logger = logger or logging
    work = runtime.work_path
    input_path = runtime.input_path
    boot = boot or findfile_func(f'{name}.img', input_path)
    if not boot:
        runtime.output.log(message(
            'boot_image_origin_missing',
            'Original {name}.img is missing. Cannot repack {name}.img.',
            name=name,
        ))
        return None
    source = source or os.path.join(work, name)
    if not exists_func(source):
        runtime.output.log(message('boot_image_source_missing', 'Cannot find unpacked {name} folder.', name=name))
        return None

    if isfile_func(os.path.join(source, 'second_order')):
        runtime.output.log('Repack Rk resource...')
        rsce_repack_func(os.path.join(source, 'second_dump'), os.path.join(source, 'second'), os.path.join(source, 'second_order'))
        runtime.output.log('Repack Rk resource successfully...')

    flag = ''
    if isdir_func(os.path.join(source, 'ramdisk')) and runtime.boot_skip_ramdisk == '0':
        cpio_name = 'cpio.exe' if os.name != 'posix' else 'cpio'
        cpio_path = findfile_func(cpio_name, runtime.tool_bin)
        if not cpio_path:
            runtime.output.log(f'Cannot find {cpio_name}. Failed to repack ramdisk.')
            return 1
        cpio_path = cpio_path.replace('\\', '/')
        cpio_command = shlex.quote(cpio_path)
        with _working_directory(os.path.join(source, 'ramdisk')):
            if call_func(['busybox', 'ash', '-c', f'find | sed 1d | {cpio_command} -H newc -R 0:0 -o -F ../ramdisk-new.cpio']) != 0:
                runtime.output.log('Failed to repack ramdisk.')
                return 1
        with open(os.path.join(source, 'comp'), 'r', encoding='utf-8') as compf:
            comp = compf.read()
        runtime.output.log(f'Compressing:{comp}')
        if comp != 'unknown':
            with _working_directory(source):
                if call_func(['magiskboot', f'compress={comp}', 'ramdisk-new.cpio']) != 0:
                    runtime.output.log('Failed to pack Ramdisk...')
                    if exists_func('ramdisk-new.cpio'):
                        remove_func('ramdisk-new.cpio')
                    return 1
                extension = 'gz' if comp == 'gzip' else comp.split('_')[0]
                compressed_ramdisk = f'ramdisk-new.cpio.{extension}'
                if not exists_func(compressed_ramdisk):
                    runtime.output.log('Failed to pack Ramdisk: compressed output is missing.')
                    return 1
                try:
                    remove_func('ramdisk.cpio')
                except FileNotFoundError:
                    pass
                except OSError:
                    logger.exception('Failed to remove previous ramdisk.cpio')
                    return 1
                rename_func(compressed_ramdisk, 'ramdisk.cpio')
        else:
            with _working_directory(source):
                if exists_func('ramdisk.cpio'):
                    remove_func('ramdisk.cpio')
                if exists_func('ramdisk-new.cpio'):
                    rename_func('ramdisk-new.cpio', 'ramdisk.cpio')
                else:
                    runtime.output.log('Failed to repack ramdisk.')
                    return 1
        runtime.output.log(f'Ramdisk Compression:{comp}')
        if comp == 'unknown':
            flag = '-n'
        runtime.output.log('Successfully packed Ramdisk..')

    with _working_directory(source):
        command = ['magiskboot', 'repack']
        if flag:
            command.append(flag)
        command.append(boot)
        if call_func(command) != 0:
            runtime.output.log(message('boot_image_repack_failed', 'Failed to pack {name}.img.', name=name))
            return None

    new_boot_path = os.path.join(source, 'new-boot.img')
    if not isfile_func(new_boot_path):
        runtime.output.log(message('boot_image_output_missing', 'Failed to pack {name}.img: magiskboot did not produce new-boot.img.', name=name))
        return None
    os.makedirs(runtime.output_path, exist_ok=True)
    output_boot_path = os.path.join(runtime.output_path, f'{name}.img')
    if isfile_func(output_boot_path):
        remove_func(output_boot_path)
    rename_func(new_boot_path, output_boot_path)
    try:
        rmdir_func(source)
    except OSError:
        runtime.output.log(message('operation_failed', 'Operation failed: {item}', item=name))
    runtime.output.log(message('boot_image_repack_success', 'Successfully packed {name}.img.', name=name))
    return True


__all__ = ['BootImageRuntimeContext', 'build_runtime_context', 'repack_boot_image', 'unpack_boot_image']
