from __future__ import annotations

from src.app.runtime.contexts.contracts import ProjectMenuProtocol, UnpackViewProtocol



def resolve_project_import_ui_targets(*, project_menu: ProjectMenuProtocol | None = None, unpack_gui: UnpackViewProtocol | None = None):
    if project_menu is None or unpack_gui is None:
        from src.app.runtime.window_access import require_project_menu, require_unpack_view
        from src.app.runtime.phases import get_registered_bootstrap_ui_runtime

        bundle = get_registered_bootstrap_ui_runtime()
        if bundle is not None:
            project_menu = project_menu or bundle.project_menu
            unpack_gui = unpack_gui or bundle.unpack_view
        project_menu = project_menu or require_project_menu()
        unpack_gui = unpack_gui or require_unpack_view()
    return project_menu, unpack_gui


__all__ = [
    'resolve_project_import_ui_targets',
]
