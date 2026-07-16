from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from src.core import ext4
from src.logic.projects.unpack.candidate_service import (
    list_pack_folder_candidates,
    list_payload_pack_candidates,
    read_image_metadata,
)
from src.logic.projects.unpack.models import ImageMetadata, PackFolderCandidate, UnpackCandidate
from src.logic.projects.unpack.registry import list_candidates as list_unpack_candidates


class UnpackWorkspaceService:
    """Read unpack workspace data without depending on application or UI state."""

    def __init__(
        self,
        *,
        json_edit_cls,
        gettype_func: Callable[[str], str],
        exists: Callable[[str], bool] = os.path.exists,
        listdir: Callable[[str], list[str]] = os.listdir,
        is_file: Callable[[str], bool] = os.path.isfile,
        is_dir: Callable[[str], bool] = os.path.isdir,
        get_size: Callable[[str], int] = os.path.getsize,
        join: Callable[..., str] = os.path.join,
        ext4_volume_factory: Callable[[str], Any] = ext4.Volume,
    ) -> None:
        self._json_edit_cls = json_edit_cls
        self._gettype = gettype_func
        self._exists = exists
        self._listdir = listdir
        self._is_file = is_file
        self._is_dir = is_dir
        self._get_size = get_size
        self._join = join
        self._ext4_volume_factory = ext4_volume_factory

    def list_unpack_items(
        self,
        input_path: str,
        format_name: str,
    ) -> tuple[UnpackCandidate, ...]:
        if not input_path or not self._exists(input_path) or not self._is_dir(input_path):
            return ()
        return tuple(list_unpack_candidates(format_name, input_path))

    def _read_parts_info(self, work_path: str) -> dict[str, str]:
        path = self._join(work_path, 'config', 'parts_info')
        if not self._exists(path):
            return {}
        data = self._json_edit_cls(path).read()
        return data if isinstance(data, dict) else {}

    def list_payload_candidates(self, input_path: str) -> tuple[UnpackCandidate, ...]:
        return list_payload_pack_candidates(
            input_path,
            {},
            listdir=self._listdir,
            is_file=self._is_file,
            get_size=self._get_size,
            get_type=self._gettype,
        )

    def list_pack_folders(self, work_path: str) -> tuple[PackFolderCandidate, ...]:
        return list_pack_folder_candidates(
            work_path,
            self._read_parts_info(work_path),
            listdir=self._listdir,
            is_dir=self._is_dir,
        )

    def read_image_metadata(self, image_path: str) -> ImageMetadata | None:
        return read_image_metadata(
            image_path,
            exists=self._exists,
            get_size=self._get_size,
            get_type=self._gettype,
            ext4_volume_factory=self._ext4_volume_factory,
        )

    def resolve_selected_image_path(
        self,
        input_path: str,
        selected_items: list[str],
        current_format: str,
    ) -> str | None:
        if len(selected_items) != 1 or current_format != 'img':
            return None
        image_path = self._join(input_path, selected_items[0] + '.img')
        return image_path if self._exists(image_path) else None

    def workspace_exists(self, work_path: str) -> bool:
        return self._exists(work_path)


__all__ = ['UnpackWorkspaceService']
