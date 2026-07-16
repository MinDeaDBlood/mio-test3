from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol


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


class UnpackPresenter:
    """Format unpack models and derive view only state."""

    def __init__(self, *, human_size: Callable[[int], str]):
        self._human_size = human_size

    @staticmethod
    def build_mode_state(is_unpack_mode: bool) -> UnpackModeState:
        return UnpackModeState(
            format_state="readonly" if is_unpack_mode else "disabled",
            should_use_pack_folders=not is_unpack_mode,
        )

    def format_unpack_candidates(
        self,
        format_name: str,
        candidates: list[UnpackCandidateProtocol] | tuple[UnpackCandidateProtocol, ...],
    ) -> list[tuple[str, str]]:
        result: list[tuple[str, str]] = []
        for candidate in candidates:
            if format_name == "payload" and candidate.size_bytes is not None:
                label = f"{candidate.name}{self._human_size(candidate.size_bytes):>10}"
            elif candidate.detected_type:
                label = f"{candidate.name} [{candidate.detected_type}]"
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
                f"{candidate.name} [{candidate.detected_type or 'img'}] ({self._human_size(candidate.size_bytes or 0)})",
                candidate.name,
            )
            for candidate in candidates
        ]

    @staticmethod
    def format_pack_folders(
        candidates: tuple[PackFolderCandidateProtocol, ...],
    ) -> list[tuple[str, str]]:
        return [
            (f"{candidate.name} [{candidate.filesystem_type}]", candidate.name)
            for candidate in candidates
        ]

    @staticmethod
    def format_image_metadata(
        metadata: ImageMetadataProtocol | None,
    ) -> list[list[object]]:
        if metadata is None:
            return []
        rows: list[list[object]] = [
            ["Path", metadata.path],
            ["Type", metadata.file_type],
            ["Size", metadata.size_bytes],
        ]
        rows.extend([list(row) for row in metadata.extra_rows])
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
