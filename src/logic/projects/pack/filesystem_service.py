from __future__ import annotations

import logging
import os
import time

from src.core.ota_dat import img2sdat
from src.core.process_runner import call
from src.logic.common.messages import message
from src.logic.common.service_output import ServiceOutput, build_service_output
from src.logic.projects.common.workspace_service import rmdir
from src.logic.projects.pack.partition_size import (
    estimate_directory_image_size,
    format_image_size_estimate,
    normalize_ext_image_size,
    update_dynamic_partition_size,
)


class GetFolderSize:
    def __init__(self, dir_: str, num: int = 1, get: int = 2, list_f: str | None = None, output: ServiceOutput | None = None):
        self.rsize_v: int
        self.num = num
        self.get = get
        self.list_f = list_f
        self.dname = os.path.basename(dir_)
        self.output = output or build_service_output()
        self.size = estimate_directory_image_size(dir_)
        if self.get == 1:
            self.rsize_v = self.size
        else:
            self.rsize(self.size, self.num)

    def rsize(self, size: int, num: int):
        self.output.log(f'{self.dname} Size : {format_image_size_estimate(size)}')
        self.rsize_v = normalize_ext_image_size(size)
        if self.get == 3:
            self.rsizelist(self.dname, self.rsize_v, self.list_f, output=self.output)
        self.rsize_v = int(self.rsize_v / num)

    @staticmethod
    def rsizelist(part_name, size, file, *, output: ServiceOutput | None = None):
        update_dynamic_partition_size(part_name, size, file, output=output)


def datbr(work: str, name: str, brl: str | int, dat_ver: int = 4, *, output: ServiceOutput | None = None) -> bool:
    output = output or build_service_output()
    output.log(message('building_image', 'Building image {item}', item=name))
    if not os.path.exists(f'{work}/{name}.img'):
        output.log(message('transfer_list_created', 'Transfer list created for {item}', item=f'{work}/{name}.img'))
        return False
    img2sdat(f'{work}/{name}.img', work, dat_ver, name)
    if os.access(f'{work}/{name}.new.dat', os.F_OK):
        image_path = f'{work}/{name}.img'
        try:
            os.remove(image_path)
        except OSError:
            logging.exception('pack.filesystem.datbr.remove_source_image_failed: partition=%s; image_path=%s', name, image_path)
    if brl == 'dat':
        output.log(message('converting_image', 'Converting image {item}', item=name))
        return True
    output.log(message('compressing', 'Compressing {item} as {format}', item=name, format='br'))
    if call(['brotli', '-q', str(brl), '-j', '-w', '24', f'{work}/{name}.new.dat', '-o', f'{work}/{name}.new.dat.br']) != 0:
        return False
    new_dat_path = f'{work}/{name}.new.dat'
    if os.access(new_dat_path, os.F_OK):
        try:
            os.remove(new_dat_path)
        except OSError:
            logging.exception('pack.filesystem.datbr.remove_intermediate_dat_failed: partition=%s; path=%s', name, new_dat_path)
    output.log(message('compression_complete', 'Compression completed for {item} as {format}', item=name, format='br'))
    return True


def _require_metadata(paths: tuple[str, ...], *, name: str, output: ServiceOutput) -> bool:
    invalid = [
        path
        for path in paths
        if not os.path.isfile(path) or os.path.getsize(path) == 0
    ]
    if not invalid:
        return True
    for path in invalid:
        output.log(message('file_not_found', 'Required metadata file is missing or empty: {item}', item=path))
    output.log(message('operation_failed', 'Operation failed: {item}', item=name))
    return False


def mkerofs(name: str, format_, work, work_output, level, old_kernel: bool = False, UTC: int | None = None, *, output: ServiceOutput | None = None):
    output = output or build_service_output()
    fs_config_path = f'{work}/config/{name}_fs_config'
    contexts_path = f'{work}/config/{name}_file_contexts'
    if not _require_metadata((fs_config_path, contexts_path), name=name, output=output):
        return 1
    os.makedirs(work_output, exist_ok=True)
    if not UTC:
        UTC = int(time.time())
    output.log(message('compressing', 'Compressing {item} as {format}', item=name, format=f'{format_},{level}'))
    extra_ = f'{format_},{level}' if format_ != 'lz4' else format_
    other_ = ['-E', 'legacy-compress'] if old_kernel else []
    cmd = [
        'mkfs.erofs',
        *other_,
        f'-z{extra_}',
        '-T',
        f'{UTC}',
        f'--mount-point=/{name}',
        f'--product-out={work}',
        f'--fs-config-file={fs_config_path}',
        f'--file-contexts={contexts_path}',
        f'{work_output}/{name}.img',
        f'{work}/{name}/',
    ]
    return call(cmd, out=True)


def make_ext4fs(name: str, work: str, work_output, sparse: bool = False, size: int = 0, UTC: int | None = None, has_contexts: bool = True, *, output: ServiceOutput | None = None):
    output = output or build_service_output()
    fs_config_path = f'{work}/config/{name}_fs_config'
    if not _require_metadata((fs_config_path,), name=name, output=output):
        return 1
    if not has_contexts:
        output.log('Warning:file_context not found!!!')
    os.makedirs(work_output, exist_ok=True)
    output.log(message('packing', 'Packing {item}', item=name))
    if not UTC:
        UTC = int(time.time())
    if not size:
        size = GetFolderSize(work + name, 1, 3, f'{work}/dynamic_partitions_op_list', output=output).rsize_v
    output.log(f'{name}:[{size}]')
    context_cmd = ['-S', f'{work}/config/{name}_file_contexts'] if has_contexts else []
    command = [
        'make_ext4fs',
        '-J',
        '-T',
        f'{UTC}',
        '-s' if sparse else '',
        *context_cmd,
        '-l',
        f'{size}',
        '-C',
        fs_config_path,
        '-L',
        name,
        '-a',
        f'/{name}',
        f'{work_output}/{name}.img',
        work + name,
    ]
    return call(command)


def make_f2fs(name: str, work: str, work_output: str, UTC: int | None = None, *, output: ServiceOutput | None = None):
    output = output or build_service_output()
    fs_config_path = f'{work}/config/{name}_fs_config'
    contexts_path = f'{work}/config/{name}_file_contexts'
    if not _require_metadata((fs_config_path, contexts_path), name=name, output=output):
        return 1
    output.log(message('packing', 'Packing {item}', item=name))
    size = GetFolderSize(work + name, 1, 1, output=output).rsize_v
    output.log(f'{name}:[{size}]')
    size_f2fs = int(((54 * 1024 * 1024) + size) * 1.15) + 1
    if not UTC:
        UTC = int(time.time())
    os.makedirs(work_output, exist_ok=True)
    image_path = f'{work_output}/{name}.img'
    with open(image_path, 'wb') as handle:
        handle.truncate(size_f2fs)
    if call(['mkfs.f2fs', image_path, '-O', 'extra_attr', '-O', 'inode_checksum', '-O', 'sb_checksum', '-O', 'compression', '-f']) != 0:
        rmdir(image_path)
        return 1
    result = call([
        'sload.f2fs',
        '-f', work + name,
        '-C', fs_config_path,
        '-T', f'{UTC}',
        '-s', contexts_path,
        '-t', f'/{name}',
        '-c', image_path,
    ])
    if result != 0:
        rmdir(image_path)
    return result


def mke2fs(name: str, work: str, sparse: bool, work_output: str, size: int = 0, UTC: int | None = None, *, output: ServiceOutput | None = None):
    output = output or build_service_output()
    fs_config_path = f'{work}/config/{name}_fs_config'
    contexts_path = f'{work}/config/{name}_file_contexts'
    if not _require_metadata((fs_config_path, contexts_path), name=name, output=output):
        return 1
    os.makedirs(work_output, exist_ok=True)
    if isinstance(size, str):
        size = int(size)
    output.log(message('packing', 'Packing {item}', item=name))
    size = GetFolderSize(work + name, 4096, 3, f'{work}/dynamic_partitions_op_list', output=output).rsize_v if not size else size / 4096
    output.log(f'{name}:[{size}]')
    if not UTC:
        UTC = int(time.time())
    if call([
        'mke2fs',
        '-O',
        '^has_journal,^metadata_csum,extent,huge_file,^flex_bg,^64bit,uninit_bg,dir_nlink,extra_isize',
        '-L',
        name,
        '-I',
        '256',
        '-M',
        f'/{name}',
        '-m',
        '0',
        '-t',
        'ext4',
        '-b',
        '4096',
        f'{work_output}/{name}_new.img',
        f'{int(size)}',
    ]) != 0:
        rmdir(f'{work_output}/{name}_new.img')
        output.log(message('operation_failed', 'Operation failed: {item}', item=name))
        return 1
    ret = call([
        'e2fsdroid',
        '-e',
        '-T',
        f'{UTC}',
        '-S',
        contexts_path,
        '-C',
        fs_config_path,
        '-a',
        f'/{name}',
        '-f',
        f'{work}/{name}',
        f'{work_output}/{name}_new.img',
    ], out=not os.name == 'posix')
    if ret != 0:
        rmdir(f'{work_output}/{name}_new.img')
        output.log(message('operation_failed', 'Operation failed: {item}', item=name))
        return 1
    if sparse:
        new_image_path = f'{work_output}/{name}_new.img'
        sparse_image_path = f'{work_output}/{name}.img'
        if call(['img2simg', new_image_path, sparse_image_path]) != 0 or not os.path.isfile(sparse_image_path):
            output.log(message('operation_failed', 'Operation failed: {item}', item=name))
            return 1
        try:
            os.remove(new_image_path)
        except OSError:
            logging.exception('pack.filesystem.mke2fs.remove_raw_after_sparse_failed: partition=%s; image_path=%s', name, new_image_path)
    else:
        target_image_path = f'{work_output}/{name}.img'
        new_image_path = f'{work_output}/{name}_new.img'
        if os.path.isfile(target_image_path):
            try:
                os.remove(target_image_path)
            except OSError:
                logging.exception('pack.filesystem.mke2fs.remove_existing_target_failed: partition=%s; image_path=%s', name, target_image_path)
        os.rename(new_image_path, target_image_path)
    return 0


__all__ = ['GetFolderSize', 'datbr', 'make_ext4fs', 'make_f2fs', 'mke2fs', 'mkerofs']
