from __future__ import annotations

import logging
import os
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from src.core.dynamic_partitions import dynamic_list_reader, generate_dynamic_list
from src.core.file_types import gettype, is_empty_img
from src.core.image_size import image_logical_size
from src.core.json_store import JsonEdit


PACKABLE_SUPER_IMAGE_TYPES = frozenset({'ext', 'erofs', 'f2fs', 'sparse'})
DEFAULT_BLOCK_DEVICE_NAME = 'super'
DEFAULT_GROUP_NAME = 'qti_dynamic_partitions'


def _base_group_name(name: str) -> str:
    if name.endswith('_a') or name.endswith('_b'):
        return name[:-2]
    return name


@dataclass(frozen=True)
class PackableSuperImage:
    name: str
    image_type: str
    empty: bool = False
    selected: bool = False


@dataclass(frozen=True)
class PackSuperInitialState:
    block_device_name: str | None = None
    super_size: int | None = None
    group_name: str | None = None
    super_type: int | None = None
    selected: tuple[str, ...] = ()


@dataclass(frozen=True)
class SuperSizeValidationResult:
    valid: bool
    suggested_size: int
    missing: tuple[str, ...] = ()


def _image_path(work: str | os.PathLike[str], name: str) -> Path:
    return Path(work) / f'{name}.img'


def _source_paths(work: str | os.PathLike[str] | Iterable[str | os.PathLike[str]]) -> tuple[Path, ...]:
    if isinstance(work, (str, os.PathLike)):
        candidates = (Path(work),)
    else:
        candidates = tuple(Path(path) for path in work)
    return tuple(dict.fromkeys(path.resolve() for path in candidates))


def _resolve_image_path(
    work: str | os.PathLike[str] | Iterable[str | os.PathLike[str]],
    name: str,
) -> Path | None:
    for source_path in _source_paths(work):
        image_path = _image_path(source_path, name)
        if image_path.exists():
            return image_path
    return None


def scan_packable_super_images(work: str | os.PathLike[str] | Iterable[str | os.PathLike[str]], selected: Iterable[str] = ()) -> tuple[PackableSuperImage, ...]:
    selected_set = set(selected)
    entries: list[PackableSuperImage] = []
    seen: set[str] = set()
    for work_path in _source_paths(work):
        if not work_path.exists():
            logging.warning('pack.super.state.scan_missing_work_path: work=%s', work_path)
            continue
        for file_name in sorted(os.listdir(work_path)):
            if not file_name.endswith('.img'):
                continue
            image_path = work_path / file_name
            name = file_name[:-4]
            if name in seen:
                continue
            try:
                if is_empty_img(str(image_path)):
                    entries.append(PackableSuperImage(name=name, image_type='empty', empty=True, selected=name in selected_set))
                    seen.add(name)
                    continue
                file_type = gettype(str(image_path))
            except (OSError, ValueError, EOFError, struct.error):
                logging.exception('pack.super.state.scan_image_failed: image_path=%s', image_path)
                continue
            if file_type in PACKABLE_SUPER_IMAGE_TYPES:
                entries.append(PackableSuperImage(name=name, image_type=file_type, selected=name in selected_set))
                seen.add(name)
    return tuple(entries)


def load_pack_super_initial_state(work: str | os.PathLike[str]) -> PackSuperInitialState:
    work_path = Path(work)
    state = PackSuperInitialState()
    state = _load_parts_info_state(work_path, state)
    state = _load_dynamic_partitions_state(work_path, state)
    return state


def _load_parts_info_state(work_path: Path, state: PackSuperInitialState) -> PackSuperInitialState:
    parts_info = work_path / 'config' / 'parts_info'
    if not parts_info.exists():
        return state
    try:
        data = JsonEdit(str(parts_info)).read().get('super_info')
        if not isinstance(data, dict):
            raise TypeError('super_info is not dict')
    except (OSError, TypeError, ValueError):
        logging.exception('pack.super.state.read_parts_info_failed: parts_info=%s', parts_info)
        return state

    block_device_name = state.block_device_name
    super_size = state.super_size
    selected: list[str] = list(state.selected)

    for item in data.get('block_devices', []):
        if isinstance(item, dict):
            block_device_name = item.get('name', block_device_name or DEFAULT_BLOCK_DEVICE_NAME)
            if isinstance(item.get('size'), int):
                super_size = item.get('size')
    # Do not initialize the UI group selector from parts_info.group_table.
    # parts_info describes the source super metadata and can contain slot-specific
    # names such as main_b; the pack dialog should keep its explicit preset unless
    # the user has a generated dynamic_partitions_op_list.
    for item in data.get('partition_table', []):
        if isinstance(item, dict):
            name = item.get('name')
            if isinstance(name, str) and name not in selected:
                selected.append(name)

    return PackSuperInitialState(
        block_device_name=block_device_name,
        super_size=super_size,
        group_name=state.group_name,
        super_type=state.super_type,
        selected=tuple(selected),
    )


def _load_dynamic_partitions_state(work_path: Path, state: PackSuperInitialState) -> PackSuperInitialState:
    list_file = work_path / 'dynamic_partitions_op_list'
    if not list_file.exists():
        return state
    try:
        data = dynamic_list_reader(str(list_file))
    except (OSError, KeyError, IndexError, TypeError, ValueError):
        logging.exception('pack.super.state.read_dynamic_list_failed: list_file=%s', list_file)
        return state

    if len(data) > 1:
        first, second = data
        first_base = _base_group_name(first)
        second_base = _base_group_name(second)
        if first_base == second_base:
            group_data = data[first]
            return PackSuperInitialState(
                block_device_name=state.block_device_name,
                group_name=first_base,
                super_size=state.super_size if isinstance(state.super_size, int) else int(group_data['size']),
                super_type=2,
                selected=tuple(_base_group_name(part) for part in group_data['parts']),
            )
    if len(data) == 1:
        group = next(iter(data.keys()))
        group_data = data[group]
        return PackSuperInitialState(
            block_device_name=state.block_device_name,
            group_name=_base_group_name(group),
            super_size=state.super_size if isinstance(state.super_size, int) else int(group_data['size']),
            super_type=state.super_type,
            selected=tuple(_base_group_name(part) for part in group_data['parts']),
        )
    return state


def validate_super_size(work: str | os.PathLike[str] | Iterable[str | os.PathLike[str]], selected: Iterable[str], requested_size: int) -> SuperSizeValidationResult:
    current_size = 0
    missing: list[str] = []
    for name in selected:
        image_path = _resolve_image_path(work, name)
        if image_path is None:
            missing.append(f'{name}.img')
            continue
        current_size += image_logical_size(image_path)
    if missing:
        return SuperSizeValidationResult(valid=False, suggested_size=requested_size, missing=tuple(missing))
    if current_size <= requested_size:
        return SuperSizeValidationResult(valid=True, suggested_size=requested_size)

    diff_size = current_size
    suggested_size = current_size
    for i in range(20):
        if not i:
            continue
        candidate_gib = i - 0.25
        candidate_size = (1024 ** 3) * candidate_gib
        diff = candidate_size - current_size
        if diff < 0:
            continue
        if diff < diff_size:
            diff_size = diff
        else:
            suggested_size = int(candidate_size)
            break
    return SuperSizeValidationResult(valid=False, suggested_size=int(suggested_size))


def generate_super_dynamic_list(*, group_name: str, size: int, super_type: int, part_list: list[str], work: str) -> None:
    generate_dynamic_list(group_name=group_name, size=size, super_type=super_type, part_list=part_list, work=work)


__all__ = [
    'DEFAULT_BLOCK_DEVICE_NAME',
    'DEFAULT_GROUP_NAME',
    'PACKABLE_SUPER_IMAGE_TYPES',
    'PackSuperInitialState',
    'PackableSuperImage',
    'SuperSizeValidationResult',
    'generate_super_dynamic_list',
    'load_pack_super_initial_state',
    'scan_packable_super_images',
    'validate_super_size',
]
