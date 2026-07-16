from __future__ import annotations

import os
from collections.abc import Callable, Iterable

from .models import ImageMetadata, PackFolderCandidate, UnpackCandidate


def list_payload_pack_candidates(
    work: str,
    parts_dict: dict[str, str],
    *,
    listdir: Callable[[str], Iterable[str]],
    is_file: Callable[[str], bool],
    get_size: Callable[[str], int],
    get_type: Callable[[str], str],
) -> tuple[UnpackCandidate, ...]:
    items: list[UnpackCandidate] = []
    for file_name in listdir(work):
        if not file_name.endswith('.img'):
            continue
        partition_name = file_name[:-4]
        image_path = os.path.join(work, file_name)
        if not is_file(image_path):
            continue
        size = get_size(image_path)
        if size <= 0:
            continue
        detected_type = get_type(image_path)
        if detected_type == 'unknown':
            detected_type = 'img'
        items.append(
            UnpackCandidate(
                name=partition_name,
                detected_type=parts_dict.get(partition_name, detected_type),
                size_bytes=size,
            )
        )
    return tuple(items)


def list_pack_folder_candidates(
    work: str,
    parts_dict: dict[str, str],
    *,
    listdir: Callable[[str], Iterable[str]],
    is_dir: Callable[[str], bool],
) -> tuple[PackFolderCandidate, ...]:
    items: list[PackFolderCandidate] = []
    for folder in listdir(work):
        folder_path = os.path.join(work, folder)
        if is_dir(folder_path) and folder in parts_dict:
            items.append(PackFolderCandidate(name=folder, filesystem_type=parts_dict[folder]))
    return tuple(items)


def read_image_metadata(
    image_path: str,
    *,
    exists: Callable[[str], bool],
    get_size: Callable[[str], int],
    get_type: Callable[[str], str],
    ext4_volume_factory: Callable[[object], object] | None = None,
) -> ImageMetadata | None:
    if not exists(image_path):
        return None
    file_type = get_type(image_path)
    extra_rows: tuple[tuple[object, ...], ...] = ()
    if file_type == 'ext' and ext4_volume_factory is not None:
        with open(image_path, 'rb') as stream:
            volume = ext4_volume_factory(stream)
            extra_rows = tuple(tuple(row) for row in volume.get_info_list)
    return ImageMetadata(
        path=image_path,
        file_type=file_type,
        size_bytes=get_size(image_path),
        extra_rows=extra_rows,
    )


__all__ = ['list_pack_folder_candidates', 'list_payload_pack_candidates', 'read_image_metadata']
