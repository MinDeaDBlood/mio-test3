"""Lazy application host for the project workspace tab."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from src.app.startup_metrics import FeatureTimeline


@dataclass(frozen=True)
class ProjectWorkspaceBundle:
    project_menu: object
    unpack_view: object
    action_panel: object


class _LazyProjectUiProxy:
    def __init__(self, resolver: Callable[[], object]) -> None:
        self._resolver = resolver

    def _resolve(self):
        return self._resolver()

    def __getattr__(self, item: str):
        return getattr(self._resolve(), item)


class _LazyProjectMenuProxy(_LazyProjectUiProxy):
    def listdir(self):
        return self._resolve().listdir()

    def set_project(self, name: str):
        return self._resolve().set_project(name)

    def remove(self):
        return self._resolve().remove()


class _LazyUnpackViewProxy(_LazyProjectUiProxy):
    def refs(self, auto: bool = False):
        return self._resolve().refs(auto)


class ProjectWorkspaceHost:
    """Own lazy project workspace construction and its stable application ports."""

    def __init__(self, window) -> None:
        self._window = window
        self._workspace: ProjectWorkspaceBundle | None = None
        self.project_menu = _LazyProjectMenuProxy(self.ensure_project_menu)
        self.unpack_view = _LazyUnpackViewProxy(self.ensure_unpack_view)

    def ensure_workspace(self) -> ProjectWorkspaceBundle:
        workspace = self._workspace
        if workspace is not None:
            try:
                if workspace.unpack_view.winfo_exists():
                    return workspace
            except Exception:
                logging.exception("Cannot inspect the existing project workspace")

        from src.app.composition.project_workspace import create_project_workspace

        timeline = FeatureTimeline("project_workspace_open")
        composed = create_project_workspace(host_window=self._window)
        project_menu = composed["project_menu"]
        unpack_view = composed["unpack_view"]
        action_panel = composed["action_panel"]
        project_menu.gui()
        project_menu.listdir()
        unpack_view.gui()
        action_panel.gui()
        workspace = ProjectWorkspaceBundle(
            project_menu=project_menu,
            unpack_view=unpack_view,
            action_panel=action_panel,
        )
        self._workspace = workspace
        self._window.notepad.invalidate_focusability(self._window.tab2)
        timeline.log(logger=logging)
        return workspace

    def ensure_project_menu(self):
        return self.ensure_workspace().project_menu

    def ensure_unpack_view(self):
        return self.ensure_workspace().unpack_view

    def handle_tab_changed(self, _event: Any = None):
        try:
            selection_target = getattr(self._window.notepad, "selection_target", None)
            selected = (
                selection_target()
                if callable(selection_target)
                else self._window.notepad.select()
            )
        except Exception:
            logging.exception("Cannot read the selected main tab")
            return None
        if selected == str(self._window.tab2):
            return self.ensure_workspace()
        return None

    def install(self) -> None:
        self._window.notepad.bind(
            "<<NotebookTabChanging>>",
            self.handle_tab_changed,
            add="+",
        )
        try:
            if self._window.notepad.select() == str(self._window.tab2):
                self._window.after_idle(self.ensure_workspace)
        except Exception:
            logging.exception("Cannot schedule initial project workspace construction")


def install_lazy_project_workspace_host(window) -> ProjectWorkspaceHost:
    host = ProjectWorkspaceHost(window)
    host.install()
    return host


__all__ = [
    "ProjectWorkspaceBundle",
    "ProjectWorkspaceHost",
    "install_lazy_project_workspace_host",
]
