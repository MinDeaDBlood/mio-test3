from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from src.logic.projects.project_menu.service import (
    list_projects,
    resolve_project_path,
    rename_project,
    remove_project,
    create_project,
)


@dataclass(frozen=True)
class ProjectMenuResult:
    succeeded: bool
    message: str = ''
    selected_project: str = ''
    projects: tuple[str, ...] = ()


class ProjectMenuController:
    def __init__(self, *, project_manager, current_project_getter: Callable[[], str], current_project_setter: Callable[[str], None]):
        self.project_manager = project_manager
        self.current_project_getter = current_project_getter
        self.current_project_setter = current_project_setter

    def resolve_current_dir(self) -> tuple[bool, str]:
        name = self.current_project_getter()
        path = resolve_project_path(self.project_manager, name)
        if not path:
            if not name:
                return False, ''
            return False, f'Cannot open folder:\n{self.project_manager.get_work_path(name)}'
        return True, path

    def project_exists(self, name: str | None = None) -> bool:
        return self.project_manager.exist(name)

    def refresh_projects(self) -> ProjectMenuResult:
        projects = tuple(list_projects(self.project_manager))
        origin_project = self.current_project_getter()
        selected = ''
        if projects:
            if origin_project and self.project_manager.exist(origin_project):
                selected = origin_project
            else:
                selected = projects[0]
        self.current_project_setter(selected)
        return ProjectMenuResult(succeeded=True, selected_project=selected, projects=projects)

    def rename_current(self, target_name: str, *, exists_message: str, unchanged_message: str, missing_message: str) -> ProjectMenuResult:
        name = self.current_project_getter()
        result = rename_project(self.project_manager, name, target_name, exists_message=exists_message, unchanged_message=unchanged_message, missing_message=missing_message)
        projects = tuple(list_projects(self.project_manager))
        selected = result.new_name if result.succeeded else self.current_project_getter()
        if result.succeeded:
            self.current_project_setter(selected)
        return ProjectMenuResult(result.succeeded, result.message or '', selected, projects)

    def remove_current(self, *, missing_message: str) -> ProjectMenuResult:
        ok, message = remove_project(self.project_manager, self.current_project_getter(), missing_message=missing_message)
        refresh = self.refresh_projects()
        return ProjectMenuResult(ok, message or '', refresh.selected_project, refresh.projects)

    def create_new(self, name: str, *, invalid_message: str) -> ProjectMenuResult:
        result = create_project(self.project_manager, name, invalid_message=invalid_message)
        refresh = self.refresh_projects()
        return ProjectMenuResult(result.succeeded, result.message or '', refresh.selected_project, refresh.projects)
