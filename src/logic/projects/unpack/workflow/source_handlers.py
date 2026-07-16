from __future__ import annotations

import logging
import os
import struct
from pathlib import Path
import time
from typing import Any, Callable

from src.core import lpunpack, splituapp
from src.core.file_types import gettype
from src.logic.common.messages import message


def _extract_partitions_from_payload(*args, **kwargs):
    from src.core.payload_extract import extract_partitions_from_payload

    return extract_partitions_from_payload(*args, **kwargs)


def metadata_file_valid(path: str) -> bool:
    return os.path.isfile(path) and os.path.getsize(path) > 0


def normalize_super_outputs(directory: str) -> None:
    for file_name in os.listdir(directory):
        file_path = os.path.join(directory, file_name)
        if file_name.endswith('_a.img'):
            target = os.path.join(directory, file_name.replace('_a', ''))
            if os.path.exists(file_path) and os.path.exists(target):
                if Path(file_path).samefile(target):
                    os.remove(file_path)
                else:
                    os.remove(target)
                    os.rename(file_path, target)
            else:
                os.rename(file_path, target)
        if file_name.endswith('_b.img') and not os.path.getsize(file_path):
            os.remove(file_path)


def extract_payload_images(
    source: str,
    selected: list[str] | tuple[str, ...],
    *,
    output: Any,
    extract_func: Callable[..., Any] | None = None,
) -> bool:
    """Extract partition images from payload.bin into the project input folder."""

    start = time.time()
    payload_path = os.path.join(source, 'payload.bin')
    if not metadata_file_valid(payload_path):
        output.report(message('file_not_found', 'File not found: {item}', item='payload.bin'))
        return False
    output.log(message('processing', 'Processing {item}', item='payload'))
    extract_func = extract_func or _extract_partitions_from_payload
    try:
        with open(payload_path, 'rb') as stream:
            extract_func(stream, selected, source, 1)
    except (OSError, RuntimeError, ValueError, EOFError, struct.error):
        logging.exception('unpack.workflow.payload_extract_failed: payload_path=%s', payload_path)
        output.report(message('operation_failed', 'Operation failed: {item}', item='payload.bin'))
        return False
    missing = [
        partition
        for partition in selected
        if not metadata_file_valid(os.path.join(source, f'{partition}.img'))
    ]
    if missing:
        output.report(message('operation_failed', 'Operation failed: {item}', item=', '.join(missing)))
        return False
    output.log('Done! tooks: %.2f' % (time.time() - start))
    return True


def extract_super_images(
    source: str,
    selected: list[str] | tuple[str, ...],
    parts: dict,
    json_edit: Any,
    *,
    output: Any,
    get_type: Callable[[str], str] | None = None,
    get_info: Callable[[str], Any] | None = None,
    unpack_func: Callable[..., Any] | None = None,
) -> bool:
    """Extract logical partition images from super.img into the input folder."""

    get_type = get_type or gettype
    get_info = get_info or lpunpack.get_info
    unpack_func = unpack_func or lpunpack.unpack
    output.log(message('processing', 'Processing {item}', item='Super'))
    image_path = os.path.join(source, 'super.img')
    if not metadata_file_valid(image_path):
        output.report(message('file_not_found', 'File not found: {item}', item='super.img'))
        return False
    if get_type(image_path) not in {'super', 'sparse'}:
        output.report(message('operation_failed', 'Operation failed: {item}', item='super.img type'))
        return False
    try:
        parts['super_info'] = get_info(image_path)
        unpack_func(image_path, source, selected)
        normalize_super_outputs(source)
    except (OSError, RuntimeError, ValueError, EOFError, struct.error):
        logging.exception('unpack.workflow.super_extract_failed: image_path=%s', image_path)
        output.report(message('operation_failed', 'Operation failed: {item}', item='super.img'))
        return False
    missing = [
        partition
        for partition in selected
        if not metadata_file_valid(os.path.join(source, f'{partition}.img'))
    ]
    if missing:
        output.report(message('operation_failed', 'Operation failed: {item}', item=', '.join(missing)))
        return False
    json_edit.write(parts)
    parts.clear()
    return True


def extract_update_app_images(
    source: str,
    selected: list[str] | tuple[str, ...],
    *,
    extract_func: Callable[..., Any] | None = None,
) -> bool:
    """Extract images from UPDATE.APP into input without unpacking their filesystems."""

    extract_func = extract_func or splituapp.extract
    source_path = os.path.join(source, 'UPDATE.APP')
    if not metadata_file_valid(source_path):
        return False
    extract_func(source_path, source, selected)
    return all(
        metadata_file_valid(os.path.join(source, f'{partition}.img'))
        for partition in selected
    )


__all__ = [
    'extract_payload_images',
    'extract_super_images',
    'extract_update_app_images',
    'metadata_file_valid',
    'normalize_super_outputs',
]
