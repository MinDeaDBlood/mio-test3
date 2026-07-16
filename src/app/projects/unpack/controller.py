from __future__ import annotations

from src.logic.projects.unpack.models import ImageMetadata, PackFolderCandidate, UnpackCandidate
from src.logic.projects.unpack.registry import run_unpack
from src.logic.projects.unpack.workspace_service import UnpackWorkspaceService


class UnpackWorkspaceController:
    """Coordinate unpack use cases using an explicit workspace service."""

    def __init__(self, *, project_manager, workspace_service: UnpackWorkspaceService, unpack_func, logger=None):
        self.project_manager = project_manager
        self.workspace_service = workspace_service
        self.unpack_func = unpack_func
        self.logger = logger

    def project_exists(self) -> bool:
        return self.project_manager.exist()

    def current_work_path(self) -> str:
        return self.project_manager.current_work_path()

    def current_input_path(self) -> str:
        return self.project_manager.current_input_path()

    def list_unpack_items(self, format_name: str) -> list[UnpackCandidate]:
        if not self.project_exists():
            return []
        return list(
            self.workspace_service.list_unpack_items(
                self.current_input_path(),
                format_name,
            )
        )

    def list_payload_candidates(self) -> tuple[UnpackCandidate, ...]:
        return self.workspace_service.list_payload_candidates(self.current_input_path())

    def list_pack_folders(self) -> tuple[PackFolderCandidate, ...]:
        return self.workspace_service.list_pack_folders(self.current_work_path())

    def read_image_metadata(self, image_path: str) -> ImageMetadata | None:
        return self.workspace_service.read_image_metadata(image_path)

    def resolve_selected_image_path(self, selected_items: list[str], current_format: str) -> str | None:
        return self.workspace_service.resolve_selected_image_path(
            self.current_input_path(),
            selected_items,
            current_format,
        )

    def execute_unpack_selection(self, selected: list[str], current_format: str) -> tuple[bool, str]:
        if not selected:
            return False, 'auto'
        ok = bool(run_unpack(current_format, selected.copy(), unpack_func=self.unpack_func))
        return ok, 'payload_candidates' if ok and current_format == 'payload' else 'auto'

    def workspace_exists(self) -> bool:
        return self.workspace_service.workspace_exists(self.current_work_path())


__all__ = ['UnpackWorkspaceController']
