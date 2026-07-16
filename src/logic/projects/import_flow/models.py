from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectImportResult:
    imported: bool
    project_name: str | None = None
    project_list_changed: bool = False
    refresh_unpack: bool = False
    error: str | None = None

    @classmethod
    def success(
        cls,
        *,
        project_name: str | None,
        project_list_changed: bool = True,
        refresh_unpack: bool = True,
    ) -> 'ProjectImportResult':
        return cls(
            imported=True,
            project_name=project_name,
            project_list_changed=project_list_changed,
            refresh_unpack=refresh_unpack,
        )

    @classmethod
    def failure(cls, error: str) -> 'ProjectImportResult':
        return cls(imported=False, error=error)


__all__ = ['ProjectImportResult']
