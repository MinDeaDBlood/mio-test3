from __future__ import annotations

import logging
from typing import Callable

from src.app.projects.unpack import view_controller_keys as keys


class UnpackViewController:
    """Coordinate an unpack view through explicit view and dialog ports."""

    def __init__(
        self,
        view,
        *,
        runtime,
        controller,
        presenter,
        task_runner,
        show_info_dialog: Callable[..., object],
        texts,
        logger=None,
    ):
        self.view = view
        self.runtime = runtime
        self.controller = controller
        self.presenter = presenter
        self.task_runner = task_runner
        self.show_info_dialog = show_info_dialog
        self.texts = texts
        self.logger = logger or logging

    def _selected_format(self) -> str:
        return self.view.format_choices.value_at(self.view.fm.current())

    def show_menu(self, event):
        selected = self.view.lsg.selected.copy()
        current_format = self._selected_format()
        if self.presenter.can_show_image_context_menu(selected, current_format):
            self.view.menu.post(event.x_root, event.y_root)

    def show_image_info(self):
        selected = self.view.lsg.selected.copy()
        image_path = self.controller.resolve_selected_image_path(
            selected, self._selected_format()
        )
        if image_path is None:
            return None
        rows = self.presenter.format_image_metadata(
            self.controller.read_image_metadata(image_path)
        )
        return self.show_info_dialog(
            info_rows=rows,
            title=self.texts.resolve_required_ui_text(keys.IMAGE_INFO_DIALOG_TITLE),
        )

    def on_mode_changed(self):
        mode_state = self.presenter.build_mode_state(self.view.ch.get())
        self.view.fm.configure(state=mode_state.format_state)
        if mode_state.should_use_pack_folders:
            self.refresh_pack_folders()
        else:
            self.request_candidates()

    def refresh_payload_candidates(self):
        self.view.lsg.clear()
        if not self.controller.workspace_exists():
            self.runtime.message_pop(
                self.texts.resolve_required_ui_text(
                    keys.PAYLOAD_WORKSPACE_MISSING_MESSAGE
                )
            )
            return False
        for label, value in self.presenter.format_payload_pack_candidates(
            self.controller.list_payload_candidates()
        ):
            self.view.lsg.insert(label, value)
        return True

    def request_candidates(self, auto: bool = False):
        if auto:
            if not self.controller.project_exists():
                return False
            current = self.view.fm.current()
            for index, format_name in enumerate(self.view.format_choices.values):
                candidates = self.controller.list_unpack_items(format_name)
                if candidates:
                    self.view.fm.current(index)
                    self.apply_candidates(format_name, candidates)
                    return True
            if current >= 0:
                self.view.fm.current(current)
            self.apply_candidates(self._selected_format(), [])
            return True
        format_name = self._selected_format()
        return self.task_runner.run(
            self.controller.list_unpack_items,
            format_name,
            on_success=lambda items, form=format_name: self.apply_candidates(
                form, items or []
            ),
        )

    def apply_candidates(self, format_name: str, candidates):
        if not self.view.winfo_exists() or format_name != self._selected_format():
            return
        self.view.lsg.clear()
        for label, value in self.presenter.format_unpack_candidates(
            format_name, candidates
        ):
            self.view.lsg.insert(label, value)

    def refresh_pack_folders(self):
        self.view.lsg.clear()
        if not self.controller.workspace_exists():
            self.runtime.message_pop(
                self.texts.resolve_required_ui_text(
                    keys.PACK_FOLDERS_WORKSPACE_MISSING_MESSAGE
                )
            )
            return False
        for label, value in self.presenter.format_pack_folders(
            self.controller.list_pack_folders()
        ):
            self.view.lsg.insert(label, value)
        return True

    def start_action(self):
        selected = self.view.lsg.selected.copy()
        if self.view.ch.get():
            return self.start_unpack(selected)
        return self.runtime.open_pack_partitions(selected)

    def start_unpack(self, selected):
        if not selected:
            return False
        if self.view.winfo_exists():
            self.view.update_idletasks()
        self.runtime.animation.run()
        current_format = self._selected_format()
        return self.task_runner.run(
            self.controller.execute_unpack_selection,
            selected.copy(),
            current_format,
            on_success=lambda result: self.after_unpack(*result),
            on_error=lambda exc: self._handle_unpack_error(exc),
            exclusive=True,
        )

    def _handle_unpack_error(self, error: Exception) -> None:
        self.after_unpack(False, "auto")
        self.runtime.message_pop(str(error))

    def after_unpack(self, ok: bool, refresh_mode: str):
        self.runtime.animation.stop()
        if not self.view.winfo_exists():
            return
        if not ok:
            return
        if refresh_mode == "payload_candidates":
            self.refresh_payload_candidates()
        else:
            self.request_candidates(auto=True)


__all__ = ["UnpackViewController"]
