from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable

from src.logic.projects.common.runtime_context import ProjectImportRuntimeContext
from src.logic.projects.import_flow.models import ProjectImportResult
from src.logic.projects.import_flow.service import copy_project, unpackrom


@dataclass(frozen=True)
class ProjectImportViewActions:
    refresh_project_list: Callable[[], None]
    select_project: Callable[[str], None]
    refresh_unpack: Callable[[bool], None]
    confirm_ofp_mtk_decrypt: Callable[[], bool]


class ProjectImportController:
    def __init__(self, *, runtime: ProjectImportRuntimeContext, view_actions: ProjectImportViewActions) -> None:
        self._runtime = runtime
        self._view_actions = view_actions

    def import_path(self, path: str) -> ProjectImportResult:
        source = Path(path)
        runtime = self._runtime
        if source.is_file() and source.suffix.lower() == '.ofp':
            runtime = replace(runtime, ofp_mtk_decrypt=self._view_actions.confirm_ofp_mtk_decrypt())
        result = copy_project(str(source), runtime=runtime) if source.is_dir() else unpackrom(str(source), runtime=runtime)
        self._apply_result(result)
        return result

    def import_file(self, path: str) -> ProjectImportResult:
        source = Path(path)
        runtime = self._runtime
        if source.suffix.lower() == '.ofp':
            runtime = replace(runtime, ofp_mtk_decrypt=self._view_actions.confirm_ofp_mtk_decrypt())
        result = unpackrom(str(source), runtime=runtime)
        self._apply_result(result)
        return result

    def _apply_result(self, result: ProjectImportResult) -> None:
        if not result.imported:
            return
        if result.project_list_changed:
            self._view_actions.refresh_project_list()
        if result.project_name:
            self._view_actions.select_project(result.project_name)
        if result.refresh_unpack:
            self._view_actions.refresh_unpack(True)


__all__ = ['ProjectImportController', 'ProjectImportViewActions']
