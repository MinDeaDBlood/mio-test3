from __future__ import annotations
import logging
import os
from src.core.ota_dat import Sdat2img
from src.core.compression import Unxz
from src.core.process_runner import call
from src.core.file_types import gettype
from src.core.sparse_tools import img2simg, simg2img
from src.logic.common.messages import message
from src.logic.common.service_output import ServiceOutput, build_service_output
from src.logic.projects.pack.filesystem_service import datbr


RAW_IMAGE_TYPES = {'ext', 'erofs', 'super', 'f2fs'}
SKIP_IMAGE_PROBE_SUFFIXES = (
    '.new.dat',
    '.new.dat.br',
    '.new.dat.xz',
    '.patch.dat',
    '.transfer.list',
    '.list',
    '.txt',
    '.json',
    '.xml',
    '.log',
)


def _remove_if_exists(path: str) -> None:
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            logging.exception('convert.remove')

def decompress_br(work: str, filename: str, *, output: ServiceOutput | None = None) -> str | None:
    output = output or build_service_output()
    path = os.path.join(work, filename)
    if not os.path.isfile(path):
        output.log(message('file_not_found', 'File not found: {item}', item=path))
        return None
    output.log(message('processing', 'Processing {item}', item=filename))
    target_name = filename[:-3] if filename.endswith('.br') else filename
    target_path = os.path.join(work, target_name)
    if call(['brotli', '-d', '-f', path, '-o', target_path]) != 0 or not os.path.isfile(target_path):
        return None
    return target_name

def decompress_xz(work: str, filename: str, *, output: ServiceOutput | None = None) -> str | None:
    output = output or build_service_output()
    path = os.path.join(work, filename)
    if not os.path.isfile(path):
        output.log(message('file_not_found', 'File not found: {item}', item=path))
        return None
    output.log(message('processing', 'Processing {item}', item=filename))
    target_name = filename[:-3] if filename.endswith('.xz') else filename
    target_path = os.path.join(work, target_name)
    Unxz(path, remove_src=False)
    return target_name if os.path.isfile(target_path) else None

def dat_to_raw(
    work: str,
    dat_filename: str,
    basename: str,
    *,
    output: ServiceOutput | None = None,
) -> str | None:
    output = output or build_service_output()
    dat_path = os.path.join(work, dat_filename)
    transferfile = os.path.join(work, f'{basename}.transfer.list')
    if not os.path.isfile(dat_path) or not os.path.isfile(transferfile) or not os.path.getsize(dat_path):
        output.log(message('file_not_found', 'Transfer list is missing or source data is empty'))
        return None
    img_path = os.path.join(work, f'{basename}.img')
    Sdat2img(transferfile, dat_path, img_path)
    if os.access(img_path, os.F_OK):
        _remove_if_exists(dat_path)
        _remove_if_exists(transferfile)
        patch_path = os.path.join(work, f'{basename}.patch.dat')
        if os.path.exists(patch_path) and not os.path.getsize(patch_path):
            _remove_if_exists(patch_path)
        return img_path
    return None

def raw_to_sparse(work: str, basename: str) -> bool:
    return bool(img2simg(os.path.join(work, f'{basename}.img')))

def raw_to_dat_or_br(work: str, basename: str, output: str) -> bool:
    level = 'dat' if output == 'dat' else 0
    return bool(datbr(work, basename, level))

def sparse_to_raw(work: str, filename: str) -> bool:
    return bool(simg2img(os.path.join(work, filename)))

def _should_probe_image_candidate(name: str) -> bool:
    lower_name = name.lower()
    if lower_name.endswith(SKIP_IMAGE_PROBE_SUFFIXES):
        return False
    return lower_name.endswith('.img') or '.' not in os.path.basename(lower_name)


def iter_image_file_types(work: str):
    try:
        entries = list(os.scandir(work))
    except OSError:
        logging.exception('convert.list_candidates.scan_failed: work=%s', work)
        return
    for entry in sorted(entries, key=lambda item: item.name.lower()):
        try:
            if not entry.is_file() or not _should_probe_image_candidate(entry.name):
                continue
            file_type = gettype(entry.path)
        except OSError:
            logging.debug('convert.list_candidates.probe_failed: path=%s', entry.path, exc_info=True)
            continue
        if file_type in RAW_IMAGE_TYPES or file_type == 'sparse':
            yield entry.name, file_type


def list_sparse_candidates(work: str) -> list[str]:
    return [name for name, file_type in iter_image_file_types(work) if file_type == 'sparse']


def list_raw_candidates(work: str) -> list[str]:
    return [name for name, file_type in iter_image_file_types(work) if file_type in RAW_IMAGE_TYPES]
