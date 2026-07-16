from __future__ import annotations

from src.ui.tabs.project.unpack import view_keys as keys
from tkinter import BooleanVar, ttk

from src.ui.localization import LocalizationCatalog
from src.ui.tabs.project.unpack.layout import build_unpack_view_layout


class UnpackGui(ttk.LabelFrame):
    """Tk view for selecting partitions to pack or unpack.

    Runtime objects and use-case controllers are assembled in
    ``src.app.composition.unpack`` and attached explicitly.
    """

    def __init__(self, *, master, current_project_name, texts: LocalizationCatalog):
        super().__init__(master=master, text=texts.resolve_required_ui_text(keys.PROJECT_UNPACK_VIEW_PARTITION_LIST))
        self.texts = texts
        self.ch = BooleanVar()
        self.current_project_name = current_project_name
        self.view_controller = None
        self._layout_ready = False
        self.current_project_name.trace_add("write", self._on_project_change)

    def attach_controller(self, controller) -> None:
        if controller is None:
            raise ValueError("UnpackGui requires a view controller")
        self.view_controller = controller

    def _require_controller(self):
        if self.view_controller is None:
            raise RuntimeError("UnpackGui controller is not attached")
        return self.view_controller

    def _on_project_change(self, *_args):
        if self._layout_ready and self.winfo_exists():
            self.hd()

    def gui(self):
        build_unpack_view_layout(self)
        self._layout_ready = True
        self.refs()

    def show_menu(self, event):
        return self._require_controller().show_menu(event)

    def info(self):
        return self._require_controller().show_image_info()

    def hd(self):
        return self._require_controller().on_mode_changed()

    def refs_payload_candidates(self):
        return self._require_controller().refresh_payload_candidates()

    def refs(self, auto: bool = False):
        return self._require_controller().request_candidates(auto=auto)

    def _apply_refs(self, form: str, items):
        return self._require_controller().apply_candidates(form, items)

    def refs2(self):
        return self._require_controller().refresh_pack_folders()

    def start_action(self):
        return self._require_controller().start_action()

    def start_unpack(self, selected):
        return self._require_controller().start_unpack(selected)

    def _after_unpack(self, ok: bool, refresh_mode: str):
        return self._require_controller().after_unpack(ok, refresh_mode)


__all__ = ["UnpackGui"]
