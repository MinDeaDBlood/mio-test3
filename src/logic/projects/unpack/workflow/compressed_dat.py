"""Compressed OTA ``*.new.dat`` handling for unpack workflow.

The input folder is the only source folder. This helper reads source files from
``source`` and writes generated intermediate files only into ``work``.
"""

from __future__ import annotations

import logging
import lzma
import os
from collections.abc import Callable
from typing import Any

from src.logic.common.messages import message
from src.core.ota_dat import Sdat2img
from src.core.process_runner import call
from src.logic.common.service_output import build_service_output


def _append_split_dat_chunks(source: str, work: str, partition_name: str, *, output: Any) -> None:
    target_path = os.path.join(work, f'{partition_name}.new.dat')
    with open(target_path, 'ab') as ofd:
        for n in range(100):
            chunk_name = f'{partition_name}.new.dat.{n}'
            chunk_path = os.path.join(source, chunk_name)
            if not os.access(chunk_path, os.F_OK):
                continue
            output.log(
                message(
                    'decompressing',
                    'Decompressing {source} to {target}',
                    source=chunk_name,
                    target=f'{partition_name}.new.dat',
                )
            )
            with open(chunk_path, 'rb') as fd:
                ofd.write(fd.read())


def _decompress_xz_to_file(source_path: str, target_path: str, *, buffer_size: int = 8192) -> None:
    decompressor = lzma.LZMADecompressor()
    with open(source_path, 'rb') as in_fd, open(target_path, 'wb') as out_fd:
        while raw := in_fd.read(buffer_size):
            while True:
                chunk = decompressor.decompress(raw, max_length=buffer_size)
                out_fd.write(chunk)
                if decompressor.needs_input or decompressor.eof:
                    break
                raw = b''


def _first_existing_path(*paths: str) -> str | None:
    return next((path for path in paths if os.access(path, os.F_OK)), None)


def unpack_compressed_dat(
    source: str,
    work: str,
    partition_name: str,
    parts: dict,
    *,
    output=None,
    call_func: Callable[..., int] = call,
    sdat2img_cls: Callable[[str, str, str], Any] = Sdat2img,
) -> bool:
    """Normalize OTA dat variants and create ``work/<partition>.img`` when possible.

    Source files stay in ``input`` unchanged. Generated files are written into
    ``unpack`` and removed after they are no longer needed.
    """
    output = output or build_service_output()
    os.makedirs(work, exist_ok=True)

    image_path = os.path.join(work, f'{partition_name}.img')
    zst_path = _first_existing_path(
        os.path.join(source, f'{partition_name}.img.zst'),
        os.path.join(source, f'{partition_name}.zst'),
    )
    xz_path = os.path.join(source, f'{partition_name}.new.dat.xz')
    br_path = os.path.join(source, f'{partition_name}.new.dat.br')
    split_head_path = os.path.join(source, f'{partition_name}.new.dat.1')
    source_new_dat_path = os.path.join(source, f'{partition_name}.new.dat')
    work_new_dat_path = os.path.join(work, f'{partition_name}.new.dat')
    transferfile = os.path.join(source, f'{partition_name}.transfer.list')

    if zst_path:
        output.log(message('processing', 'Processing {item}', item=os.path.basename(zst_path)))
        result = call_func(['zstd', '-d', zst_path, '-o', image_path])
        if result != 0 or not os.path.isfile(image_path) or os.path.getsize(image_path) == 0:
            output.log(message('operation_failed', 'Operation failed: {item}', item=os.path.basename(zst_path)))
        return False

    generated_new_dat = False
    if os.access(xz_path, os.F_OK):
        output.log(message('processing', 'Processing {item}', item=f'{partition_name}.new.dat.xz'))
        _decompress_xz_to_file(xz_path, work_new_dat_path)
        generated_new_dat = True
    elif os.access(br_path, os.F_OK):
        output.log(message('processing', 'Processing {item}', item=f'{partition_name}.new.dat.br'))
        result = call_func(['brotli', '-d', br_path, '-o', work_new_dat_path])
        if result != 0:
            output.log(message('operation_failed', 'Operation failed: {item}', item=f'{partition_name}.new.dat.br'))
            return False
        generated_new_dat = True
    elif os.access(split_head_path, os.F_OK):
        _append_split_dat_chunks(source, work, partition_name, output=output)
        generated_new_dat = True

    new_dat_path = work_new_dat_path if generated_new_dat else source_new_dat_path
    if os.access(new_dat_path, os.F_OK):
        output.log(message('processing', 'Processing {item}', item=f'{partition_name}.new.dat'))
        if os.path.getsize(new_dat_path) != 0:
            if os.access(transferfile, os.F_OK):
                parts['dat_ver'] = sdat2img_cls(transferfile, new_dat_path, image_path).version
                if os.access(image_path, os.F_OK):
                    if generated_new_dat:
                        try:
                            os.remove(work_new_dat_path)
                        except FileNotFoundError:
                            pass
                        except OSError:
                            logging.exception(
                                'unpack.compressed_dat.remove_generated_new_dat_failed: partition=%s; path=%s',
                                partition_name,
                                work_new_dat_path,
                            )
                else:
                    output.log('File May Not Extracted.')
            else:
                output.log(message('transfer_list_created', 'Transfer list created'))
    return False


__all__ = ['unpack_compressed_dat']
