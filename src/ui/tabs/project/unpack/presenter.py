from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.ui.common.byte_size import format_localized_byte_size
from src.ui.common.technical_choices import technical_label
from src.ui.localization import LocalizationCatalog
from src.ui.tabs.project.unpack import presenter_keys as keys


class UnpackCandidateProtocol(Protocol):
    name: str
    detected_type: str | None
    size_bytes: int | None


class PackFolderCandidateProtocol(Protocol):
    name: str
    filesystem_type: str


class ImageMetadataProtocol(Protocol):
    path: object
    file_type: str
    size_bytes: int
    extra_rows: tuple[tuple[object, ...], ...]


@dataclass(frozen=True)
class UnpackModeState:
    format_state: str
    should_use_pack_folders: bool


_EXT4_FIELD_KEYS: dict[str, str] = {
    "magic_number": keys.EXT4_MAGIC_NUMBER,
    "volume_name": keys.EXT4_VOLUME_NAME,
    "uuid": keys.EXT4_UUID,
    "last_mounted_on": keys.EXT4_LAST_MOUNTED_ON,
    "block_size": keys.EXT4_BLOCK_SIZE,
    "block_count": keys.EXT4_BLOCK_COUNT,
    "free_inodes": keys.EXT4_FREE_INODES,
    "free_blocks": keys.EXT4_FREE_BLOCKS,
    "inodes_per_group": keys.EXT4_INODES_PER_GROUP,
    "blocks_per_group": keys.EXT4_BLOCKS_PER_GROUP,
    "inode_count": keys.EXT4_INODE_COUNT,
    "reserved_gdt_blocks": keys.EXT4_RESERVED_GDT_BLOCKS,
    "inode_size": keys.EXT4_INODE_SIZE,
    "filesystem_created": keys.EXT4_FILESYSTEM_CREATED,
    "current_size": keys.EXT4_CURRENT_SIZE,
}


class UnpackPresenter:
    """Format unpack models and derive view only state."""

    def __init__(self, *, texts: LocalizationCatalog):
        self._texts = texts

    @staticmethod
    def build_mode_state(is_unpack_mode: bool) -> UnpackModeState:
        return UnpackModeState(
            format_state="readonly" if is_unpack_mode else "disabled",
            should_use_pack_folders=not is_unpack_mode,
        )

    def _type_label(self, technical_type: str) -> str:
        return technical_label(self._texts, technical_type)

    def format_unpack_candidates(
        self,
        format_name: str,
        candidates: list[UnpackCandidateProtocol] | tuple[UnpackCandidateProtocol, ...],
    ) -> list[tuple[str, str]]:
        result: list[tuple[str, str]] = []
        for candidate in candidates:
            if format_name == "payload" and candidate.size_bytes is not None:
                label = f"{candidate.name}{format_localized_byte_size(candidate.size_bytes, texts=self._texts):>10}"
            elif candidate.detected_type:
                label = (
                    f"{candidate.name} [{self._type_label(candidate.detected_type)}]"
                )
            else:
                label = candidate.name
            result.append((label, candidate.name))
        return result

    def format_payload_pack_candidates(
        self,
        candidates: tuple[UnpackCandidateProtocol, ...],
    ) -> list[tuple[str, str]]:
        return [
            (
                f"{candidate.name} "
                f"[{self._type_label(candidate.detected_type or 'img')}] "
                f"({format_localized_byte_size(candidate.size_bytes or 0, texts=self._texts)})",
                candidate.name,
            )
            for candidate in candidates
        ]

    def format_pack_folders(
        self,
        candidates: tuple[PackFolderCandidateProtocol, ...],
    ) -> list[tuple[str, str]]:
        return [
            (
                f"{candidate.name} [{self._type_label(candidate.filesystem_type)}]",
                candidate.name,
            )
            for candidate in candidates
        ]

    def format_image_metadata(
        self,
        metadata: ImageMetadataProtocol | None,
    ) -> list[list[object]]:
        if metadata is None:
            return []
        rows: list[list[object]] = [
            [self._texts.resolve_required_ui_text(keys.METADATA_PATH), metadata.path],
            [
                self._texts.resolve_required_ui_text(keys.METADATA_TYPE),
                self._type_label(metadata.file_type),
            ],
            [
                self._texts.resolve_required_ui_text(keys.METADATA_SIZE),
                metadata.size_bytes,
            ],
        ]
        for row in metadata.extra_rows:
            if not row:
                continue
            field_id = str(row[0])
            field_key = _EXT4_FIELD_KEYS[field_id]
            rows.append(
                [self._texts.resolve_required_ui_text(field_key), *list(row[1:])]
            )
        return rows

    @staticmethod
    def can_show_image_context_menu(
        selected_items: list[str], current_format: str
    ) -> bool:
        return len(selected_items) == 1 and current_format == "img"


__all__ = [
    "ImageMetadataProtocol",
    "PackFolderCandidateProtocol",
    "UnpackCandidateProtocol",
    "UnpackModeState",
    "UnpackPresenter",
]
