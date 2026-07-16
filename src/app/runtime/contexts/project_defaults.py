from __future__ import annotations

from dataclasses import dataclass

from src.app.runtime.contexts.contracts import ProjectManagerProtocol, SettingsProtocol, VariableProtocol


@dataclass(frozen=True)
class CommonProjectDefaults:
    settings: SettingsProtocol
    project_manager: ProjectManagerProtocol
    current_project_name: VariableProtocol


__all__ = [
    'CommonProjectDefaults',
]
