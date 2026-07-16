from __future__ import annotations

from collections.abc import Callable

from src.app.localization_runtime import lang
from src.app.composition import project_import_keys as keys
from src.app.project_contexts import build_app_project_import_context
from src.app.projects.import_controller import (
    ProjectImportController,
    ProjectImportViewActions,
)
from src.app.runtime.contexts.project_ui import resolve_project_import_ui_targets
from src.app.runtime.contexts.ui import resolve_ui_host_window
from src.app.ui_feedback import build_ui_notifier
from src.app.composition.service_output import build_ui_service_output
from src.ui.warn.dialogs import ask_win


def _require_callable(target: object, name: str) -> Callable:
    if not hasattr(target, name):
        raise RuntimeError(f"Project import UI target requires callable {name}().")
    value = getattr(target, name)
    if not callable(value):
        raise RuntimeError(f"Project import UI target requires callable {name}().")
    return value


def build_project_import_controller(
    *,
    host_window=None,
    project_menu=None,
    unpack_view=None,
    confirm_ofp_mtk_decrypt: Callable[[], bool] | None = None,
) -> ProjectImportController:
    host = resolve_ui_host_window(host_window)
    project_menu, unpack_view = resolve_project_import_ui_targets(
        project_menu=project_menu,
        unpack_gui=unpack_view,
    )
    notifier = build_ui_notifier(host_window=host)
    confirm = confirm_ofp_mtk_decrypt or (
        lambda: bool(
            ask_win(lang.resolve_required_ui_text(keys.OFP_PLATFORM_CONFIRMATION)) == 1
        )
    )
    view_actions = ProjectImportViewActions(
        refresh_project_list=_require_callable(project_menu, "listdir"),
        select_project=_require_callable(project_menu, "set_project"),
        refresh_unpack=_require_callable(unpack_view, "refs"),
        confirm_ofp_mtk_decrypt=confirm,
    )
    return ProjectImportController(
        runtime=build_app_project_import_context(
            output=build_ui_service_output(texts=lang, notify=notifier.show)
        ),
        view_actions=view_actions,
    )


__all__ = ["build_project_import_controller"]
