from __future__ import annotations

from src.ui.tabs.project import action_panel_keys as keys
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ActionButtonSpec:
    text: str
    command: Callable[[], object]
    threaded: bool = False
    width: int | None = None


class ProjectActionPanelController:
    def __init__(
        self,
        *,
        pack_zip: Callable[[], object],
        pack_super: Callable[[], object],
        open_notepad: Callable[[], object],
        open_convert: Callable[[], object],
    ):
        self.pack_zip = pack_zip
        self.pack_super = pack_super
        self.open_notepad = open_notepad
        self.open_convert = open_convert

    def build_action_specs(self, *, lang) -> tuple[ActionButtonSpec, ...]:
        return (
            ActionButtonSpec(
                lang.resolve_required_ui_text(keys.PROJECT_ACTION_PANEL_PRESENTER_PACK_ZIP),
                self.pack_zip,
                threaded=False,
            ),
            ActionButtonSpec(
                lang.resolve_required_ui_text(keys.PROJECT_ACTION_PANEL_PRESENTER_PACK_SUPER),
                self.pack_super,
                threaded=False,
            ),
            ActionButtonSpec(
                lang.resolve_required_ui_text(keys.PROJECT_ACTION_PANEL_PRESENTER_PLUGIN),
                self.open_notepad,
                threaded=False,
            ),
            ActionButtonSpec(
                lang.resolve_required_ui_text(keys.PROJECT_ACTION_PANEL_PRESENTER_CONVERT_IMAGE_ACTION),
                self.open_convert,
                threaded=False,
            ),
        )
