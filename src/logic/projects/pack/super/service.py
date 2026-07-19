from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict
from typing import Iterable

from src.core.image_size import android_sparse_logical_size, image_logical_size
from src.core.process_runner import call


from src.logic.projects.pack.super.models import ImageSizeInfo, PackSuperResult, PartitionImageInfo


class PackSuperValidationError(ValueError):
    """Raised when the requested super image cannot be built safely."""


def _normalize_part_list(part_list: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for part in part_list:
        name = part[:-2] if part.endswith('_b') or part.endswith('_a') else part
        if name not in normalized:
            normalized.append(name)
    return normalized


def _image_path(work: str, part: str) -> str:
    return os.path.join(work, f'{part}.img')


def _inspect_existing_image(path: str) -> ImageSizeInfo:
    physical_size = os.path.getsize(path)
    sparse_logical_size = android_sparse_logical_size(path)
    return ImageSizeInfo(
        path=path,
        logical_size=sparse_logical_size if sparse_logical_size is not None else physical_size,
        physical_size=physical_size,
        sparse=sparse_logical_size is not None,
    )


def _require_image_path(sources: tuple[str, ...], part: str) -> str:
    for source in sources:
        for candidate in (part, f'{part}_a'):
            image_path = _image_path(source, candidate)
            if os.path.exists(image_path):
                return image_path
    raise FileNotFoundError(
        f'pack.super.image_missing: part={part}; sources={sources}'
    )


def _require_image_info(sources: tuple[str, ...], part: str) -> ImageSizeInfo:
    return _inspect_existing_image(_require_image_path(sources, part))


def _require_paths(work: str | None, output_dir: str | None) -> tuple[str, str]:
    if not work or not output_dir:
        raise ValueError('Super image packing requires explicit work and output_dir paths.')
    return work, output_dir


def _build_partition_infos(*, sources: tuple[str, ...], part_list: list[str], super_type: int, group_name: str, attrib: str) -> tuple[PartitionImageInfo, ...]:
    infos: list[PartitionImageInfo] = []
    if super_type == 1:
        for part in part_list:
            infos.append(PartitionImageInfo(partition_name=part, image_name=part, image=_require_image_info(sources, part), group_name=group_name, attributes=attrib))
        return tuple(infos)

    for part in part_list:
        infos.append(PartitionImageInfo(partition_name=f'{part}_a', image_name=part, image=_require_image_info(sources, part), group_name=f'{group_name}_a', attributes=attrib))
    for part in part_list:
        slot_b_path = next(
            (path for source in sources if os.path.exists(path := _image_path(source, f'{part}_b'))),
            None,
        )
        slot_b_info = _inspect_existing_image(slot_b_path) if slot_b_path else None
        infos.append(PartitionImageInfo(partition_name=f'{part}_b', image_name=f'{part}_b', image=slot_b_info, group_name=f'{group_name}_b', attributes=attrib))
    return tuple(infos)


def _append_partition_args(command: list[str], partition: PartitionImageInfo) -> None:
    command += ['--partition', f'{partition.partition_name}:{partition.attributes}:{partition.partition_size}:{partition.group_name}']
    if partition.image is not None:
        command += ['--image', f'{partition.partition_name}={partition.image.path}']


def _log_pack_plan(*, work: str, output_dir: str, sparse: bool, block_device_name: str, group_name: str, size: int, super_type: int, partitions: tuple[PartitionImageInfo, ...]) -> None:
    logging.info(
        'pack.super.plan: work=%s; output_dir=%s; sparse=%s; block_device=%s; group=%s; requested_device_size=%s; super_type=%s',
        work,
        output_dir,
        sparse,
        block_device_name,
        group_name,
        size,
        super_type,
    )
    for partition in partitions:
        if partition.image is None:
            logging.info('pack.super.part: name=%s; group=%s; image=empty; logical_size=0', partition.partition_name, partition.group_name)
            continue
        logging.info(
            'pack.super.part: name=%s; group=%s; image=%s; logical_size=%s; physical_size=%s; sparse=%s',
            partition.partition_name,
            partition.group_name,
            partition.image.path,
            partition.image.logical_size,
            partition.image.physical_size,
            partition.image.sparse,
        )


def _validate_requested_size(size: int, partitions: tuple[PartitionImageInfo, ...]) -> None:
    if size <= 0:
        raise PackSuperValidationError(f'pack.super.invalid_device_size: size={size}')
    used_size = sum(partition.partition_size for partition in partitions)
    if used_size > size:
        raise PackSuperValidationError(f'pack.super.device_too_small: used_size={used_size}; requested_device_size={size}')


def _build_lpmake_command(*, sparse: bool, group_name: str, size: int, super_type: int, partitions: tuple[PartitionImageInfo, ...], output_super_path: str, block_device_name: str) -> list[str]:
    command = ['lpmake', '--metadata-size', '65536', '-super-name', block_device_name, '-metadata-slots']
    if super_type == 1:
        command += ['2', '-device', f'{block_device_name}:{size}', '--group', f'{group_name}:{size}']
        for partition in partitions:
            _append_partition_args(command, partition)
    else:
        command += ['3', '-device', f'{block_device_name}:{size}', '--group', f'{group_name}_a:{size}']
        for partition in partitions:
            if partition.group_name == f'{group_name}_a':
                _append_partition_args(command, partition)
        command += ['--group', f'{group_name}_b:{size}']
        for partition in partitions:
            if partition.group_name == f'{group_name}_b':
                _append_partition_args(command, partition)
        if super_type == 2:
            command += ['--virtual-ab']
    if sparse:
        command += ['--sparse']
    command += ['--out', output_super_path]
    return command


def _write_pack_report(*, output_dir: str, result: PackSuperResult, command: list[str]) -> str:
    report_path = os.path.join(output_dir, 'super_pack_report.json')
    payload = asdict(result)
    payload['command'] = command
    payload['size_note'] = 'For Android sparse output, physical_size can be much smaller than requested_device_size. Validate logical_size against requested_device_size.'
    with open(report_path, 'w', encoding='utf-8') as report_file:
        json.dump(payload, report_file, ensure_ascii=False, indent=2)
    return report_path


def _build_result(*, output_super_path: str, output_dir: str, sparse: bool, requested_device_size: int, partitions: tuple[PartitionImageInfo, ...], command: list[str]) -> PackSuperResult:
    output_logical_size = image_logical_size(output_super_path)
    output_physical_size = os.path.getsize(output_super_path)
    output_is_sparse = android_sparse_logical_size(output_super_path) is not None
    if output_logical_size != requested_device_size:
        raise PackSuperValidationError(
            f'pack.super.output_size_mismatch: path={output_super_path}; logical_size={output_logical_size}; requested_device_size={requested_device_size}'
        )
    result = PackSuperResult(
        output_path=output_super_path,
        report_path=os.path.join(output_dir, 'super_pack_report.json'),
        sparse=sparse,
        requested_device_size=requested_device_size,
        output_logical_size=output_logical_size,
        output_physical_size=output_physical_size,
        output_is_sparse=output_is_sparse,
        partitions=partitions,
    )
    report_path = _write_pack_report(output_dir=output_dir, result=result, command=command)
    result = PackSuperResult(
        output_path=result.output_path,
        report_path=report_path,
        sparse=result.sparse,
        requested_device_size=result.requested_device_size,
        output_logical_size=result.output_logical_size,
        output_physical_size=result.output_physical_size,
        output_is_sparse=result.output_is_sparse,
        partitions=result.partitions,
    )
    logging.info(
        'pack.super.output: path=%s; format=%s; logical_size=%s; physical_size=%s; requested_device_size=%s; report=%s',
        result.output_path,
        'sparse' if result.output_is_sparse else 'raw',
        result.output_logical_size,
        result.output_physical_size,
        result.requested_device_size,
        result.report_path,
    )
    return result


def pack_super(
    sparse: bool,
    group_name: str,
    size: int,
    super_type,
    part_list: list,
    del_: bool = False,
    return_cmd=0,
    attrib='readonly',
    output_dir: str | None = None,
    work: str | None = None,
    block_device_name: str = 'None',
    return_result: bool = False,
    source_dirs: Iterable[str] | None = None,
):
    if not block_device_name or block_device_name == 'None':
        block_device_name = 'super'
    work, output_dir = _require_paths(work, output_dir)
    sources = tuple(
        dict.fromkeys(
            os.path.abspath(path)
            for path in (work, *(source_dirs or ()))
            if path
        )
    )
    part_list = _normalize_part_list(part_list)

    output_super_path = os.path.join(output_dir, 'super.img')
    partitions = _build_partition_infos(sources=sources, part_list=part_list, super_type=int(super_type), group_name=group_name, attrib=attrib)
    _validate_requested_size(size, partitions)
    _log_pack_plan(work=work, output_dir=output_dir, sparse=sparse, block_device_name=block_device_name, group_name=group_name, size=size, super_type=int(super_type), partitions=partitions)
    command = _build_lpmake_command(
        sparse=sparse,
        group_name=group_name,
        size=size,
        super_type=int(super_type),
        partitions=partitions,
        output_super_path=output_super_path,
        block_device_name=block_device_name,
    )
    if return_cmd == 1:
        return command

    success = call(command, out=False) == 0 and os.access(output_super_path, os.F_OK)
    if not success:
        return False

    try:
        result = _build_result(
            output_super_path=output_super_path,
            output_dir=output_dir,
            sparse=sparse,
            requested_device_size=size,
            partitions=partitions,
            command=command,
        )
    except OSError:
        logging.exception('pack.super.output_size_validation_failed: path=%s; requested_device_size=%s', output_super_path, size)
        return False

    if del_:
        for img in part_list:
            image_path = _image_path(work, img)
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except OSError:
                    logging.exception('pack.super.delete_source_failed: part=%s; image_path=%s', img, image_path)
    return result if return_result else result.output_path


__all__ = ['ImageSizeInfo', 'PackSuperResult', 'PackSuperValidationError', 'pack_super']
