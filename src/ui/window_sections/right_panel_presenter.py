from __future__ import annotations

from dataclasses import dataclass

from src.ui.window_sections import right_panel_keys as keys


@dataclass(frozen=True)
class RightPanelSpec:
    title_text: str
    drop_title: str
    drop_hint: str
    stdout_buffer: str


class RightPanelController:
    def __init__(self, *, lang, stdout_obj):
        self.lang = lang
        self.stdout_obj = stdout_obj

    def build_spec(self) -> RightPanelSpec:
        return RightPanelSpec(
            title_text=self.lang.resolve_required_ui_text(keys.BRAND_TITLE),
            drop_title=self.lang.resolve_required_ui_text(keys.DROP_ROM_TITLE),
            drop_hint=self.lang.resolve_required_ui_text(keys.DROP_FILES_HINT)
            + "\n(pac ozip zip tar.md5 tar tar.gz kdz dz ops ofp ext4 erofs boot img)",
            stdout_buffer=str(self.stdout_obj.data),
        )
