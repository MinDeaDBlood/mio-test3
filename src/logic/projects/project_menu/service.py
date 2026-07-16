from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectRenameResult:
    succeeded: bool
    message: str
    new_name: str | None = None


@dataclass(frozen=True)
class ProjectCreateResult:
    succeeded: bool
    message: str
    new_name: str | None = None


def list_projects(project_manager) -> list[str]:
    return list(project_manager.get_projects())


def ensure_existing_project(project_manager, name: str) -> bool:
    return bool(name) and project_manager.exist(name)


def resolve_project_path(project_manager, name: str) -> str | None:
    if not ensure_existing_project(project_manager, name):
        return None
    path = project_manager.get_work_path(name)
    return path if path and os.path.exists(path) else None


def rename_project(project_manager, old_name: str, new_name: str, *, exists_message: str, unchanged_message: str, missing_message: str) -> ProjectRenameResult:
    if not ensure_existing_project(project_manager, old_name):
        return ProjectRenameResult(False, missing_message)
    if project_manager.exist(new_name):
        return ProjectRenameResult(False, exists_message)
    if new_name == old_name:
        return ProjectRenameResult(False, unchanged_message)
    os.rename(project_manager.get_work_path(old_name), project_manager.get_work_path(new_name))
    return ProjectRenameResult(True, '', new_name)


def remove_project(project_manager, name: str, *, missing_message: str) -> tuple[bool, str]:
    if not ensure_existing_project(project_manager, name):
        return False, missing_message
    project_manager.remove(name)
    return True, ''


def create_project(project_manager, raw_name: str, *, invalid_message: str) -> ProjectCreateResult:
    if not raw_name:
        return ProjectCreateResult(False, invalid_message)
    normalized = raw_name.replace(' ', '_')
    if not normalized.isprintable():
        return ProjectCreateResult(False, invalid_message)
    project_manager.new(normalized)
    return ProjectCreateResult(True, '', normalized)
