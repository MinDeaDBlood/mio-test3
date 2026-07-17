from __future__ import annotations

import logging
from tkinter import BOTH, LEFT, RIGHT, X, BooleanVar, Frame, IntVar, Label, StringVar
from tkinter import ttk

from src.ui.warn.dialogs import ask_win, warn_win
from src.ui.localization import LocalizationCatalog
from src.ui.common.controls import ListBox
from src.ui.common.technical_choices import build_choice_set
from src.ui.common.windowing import Toplevel
from src.ui.tabs.project.pack.super.presenter import (
    describe_pack_super_result,
    format_packable_super_image,
)
from src.ui.tabs.project.pack.super import keys


class PackSuper(Toplevel):
    """Super image pack window. Workflow operations are delegated to a controller."""

    def __init__(
        self,
        *,
        texts: LocalizationCatalog,
        default_group_name: str,
        emit,
        master=None,
    ):
        super().__init__(master=master)
        self._texts = texts
        self._emit = emit
        self.controller = None
        self._start_animation = None
        self._stop_animation = None
        self._show_error = None
        self.title(
            self._texts.resolve_required_ui_text(
                keys.PROJECT_PACK_SUPER_WINDOW_PACK_SUPER
            )
        )
        self.super_size = IntVar(value=9126805504)
        self.is_sparse = BooleanVar()
        self.super_type = IntVar(value=1)
        self.attrib = StringVar(value="readonly")
        self._group_choices = build_choice_set(
            self._texts,
            ("qti_dynamic_partitions", "main", "mot_dp_group"),
        )
        self._default_group_name = default_group_name
        self.group_name = StringVar(value=self._display_group_name(default_group_name))
        self.delete_source_file = BooleanVar(value=False)
        self.block_device_name = StringVar(value="super")
        self.selected: list[str] = []
        self._build_layout()

    def attach_controller(
        self, controller, *, start_animation, stop_animation, show_error
    ) -> None:
        if controller is None:
            raise ValueError("PackSuper requires a controller")
        self.controller = controller
        self._start_animation = start_animation
        self._stop_animation = stop_animation
        self._show_error = show_error
        self.read_list()
        self.refresh()
        self.center_on_screen(force=True)

    def _require_controller(self):
        if self.controller is None:
            raise RuntimeError("PackSuper controller is not attached")
        return self.controller

    def _build_layout(self):
        settings_frame = ttk.LabelFrame(
            self,
            text=self._texts.resolve_required_ui_text(
                keys.PROJECT_PACK_SUPER_WINDOW_PARTITION_LAYOUT
            ),
        )
        settings_frame.pack(fill=BOTH)
        attribute_frame = ttk.LabelFrame(
            self,
            text=self._texts.resolve_required_ui_text(keys.ATTRIBUTE_GROUP_TITLE),
        )
        attribute_frame.pack(fill=BOTH)
        group_frame = ttk.LabelFrame(
            self,
            text=self._texts.resolve_required_ui_text(
                keys.PROJECT_PACK_SUPER_WINDOW_SETTINGS_GROUP_TITLE
            ),
        )
        group_frame.pack(fill=BOTH)
        list_frame = ttk.LabelFrame(
            self,
            text=self._texts.resolve_required_ui_text(
                keys.PROJECT_PACK_SUPER_WINDOW_INCLUDED_PARTITIONS
            ),
        )
        list_frame.pack(fill=BOTH, expand=True)

        for text, value in [
            (self._texts.resolve_required_ui_text(keys.LAYOUT_A_ONLY_OPTION), 1),
            (self._texts.resolve_required_ui_text(keys.LAYOUT_VIRTUAL_AB_OPTION), 2),
            (self._texts.resolve_required_ui_text(keys.LAYOUT_AB_OPTION), 3),
        ]:
            ttk.Radiobutton(
                settings_frame, text=text, variable=self.super_type, value=value
            ).pack(side=LEFT, padx=10, pady=10)
        ttk.Radiobutton(
            attribute_frame,
            text=self._texts.resolve_required_ui_text(keys.ATTRIBUTE_READONLY_OPTION),
            variable=self.attrib,
            value="readonly",
        ).pack(side=LEFT, padx=10, pady=10)
        ttk.Radiobutton(
            attribute_frame,
            text=self._texts.resolve_required_ui_text(keys.ATTRIBUTE_NONE_OPTION),
            variable=self.attrib,
            value="none",
        ).pack(side=LEFT, padx=10, pady=10)

        Label(
            group_frame,
            text=self._texts.resolve_required_ui_text(
                keys.PROJECT_PACK_SUPER_WINDOW_GROUP_NAME
            ),
        ).pack(side=LEFT, padx=10, pady=10)
        self.group_combo = ttk.Combobox(
            group_frame,
            textvariable=self.group_name,
            values=self._group_choices.labels,
        )
        try:
            self.group_combo.current(
                self._group_choices.index_for(self._default_group_name)
            )
        except KeyError:
            self.group_combo.set(self._default_group_name)
        self.group_combo.pack(side=LEFT, padx=10, pady=10, fill=BOTH)
        Label(
            group_frame,
            text=self._texts.resolve_required_ui_text(
                keys.PROJECT_PACK_SUPER_WINDOW_SUPER_SIZE
            ),
        ).pack(side=LEFT, padx=10, pady=10)
        size_entry = ttk.Entry(group_frame, textvariable=self.super_size)
        size_entry.pack(side=LEFT, padx=10, pady=10)
        size_entry.bind(
            "<KeyRelease>", lambda *_: self._update_size_entry_state(size_entry)
        )

        self.tl = ListBox(
            list_frame,
            texts=self._texts,
            set_all_text=self._texts.resolve_required_ui_text(keys.SELECT_ALL_CHECKBOX),
        )
        self.tl.gui()
        self.tl.pack(padx=10, pady=10, expand=True, fill=BOTH)

        ttk.Checkbutton(
            self,
            text=self._texts.resolve_required_ui_text(
                keys.PROJECT_PACK_SUPER_WINDOW_CREATE_SPARSE_IMAGE
            ),
            variable=self.is_sparse,
            onvalue=True,
            offvalue=False,
            style="Switch.TCheckbutton",
        ).pack(padx=10, pady=10, fill=BOTH)
        actions = Frame(self)
        ttk.Checkbutton(
            actions,
            text=self._texts.resolve_required_ui_text(
                keys.PROJECT_PACK_SUPER_WINDOW_REMOVE_ORIGINAL_FILE
            ),
            variable=self.delete_source_file,
            onvalue=True,
            offvalue=False,
            style="Switch.TCheckbutton",
        ).pack(side=LEFT, padx=10, pady=10, fill=BOTH)
        ttk.Button(
            actions,
            text=self._texts.resolve_required_ui_text(keys.REFRESH_BUTTON),
            command=self.refresh,
        ).pack(side=RIGHT, padx=10, pady=10)
        self.generate_button = ttk.Button(
            actions,
            text=self._texts.resolve_required_ui_text(
                keys.PROJECT_PACK_SUPER_WINDOW_GENERATE_LIST
            ),
            command=self.generate_async,
        )
        self.generate_button.pack(side=LEFT, padx=10, pady=10, fill=BOTH)
        actions.pack(fill=X)

        ttk.Button(
            self,
            text=self._texts.resolve_required_ui_text(keys.CANCEL_BUTTON),
            command=self.destroy,
        ).pack(side=LEFT, padx=10, pady=10, fill=X, expand=True)
        ttk.Button(
            self,
            text=self._texts.resolve_required_ui_text(keys.PACK_BUTTON),
            command=self.start_async,
            style="Accent.TButton",
        ).pack(side=LEFT, padx=5, pady=5, fill=X, expand=True)

    def _display_group_name(self, value: str) -> str:
        try:
            return self._group_choices.label_for(value)
        except KeyError:
            return value

    def _internal_group_name(self) -> str:
        selected_index = self.group_combo.current()
        if selected_index >= 0:
            return self._group_choices.value_at(selected_index)
        return self.group_name.get().strip()

    def _update_size_entry_state(self, entry):
        entry.state(["!invalid" if entry.get().isdigit() else "invalid"])

    def start_async(self):
        try:
            size = self.super_size.get()
        except Exception:
            self.super_size.set(0)
            size = 0
        controller = self._require_controller()
        if not controller.project_exists():
            warn_win(
                texts=self._texts,
                text=self._texts.resolve_required_ui_text(
                    keys.PROJECT_REQUIRED_MESSAGE
                ),
                title=self._texts.resolve_required_ui_text(
                    keys.PROJECT_REQUIRED_DIALOG_TITLE
                ),
                ok=self._texts.resolve_required_ui_text(
                    keys.PROJECT_REQUIRED_DIALOG_OK_BUTTON
                ),
                master=self,
            )
            return False
        if not self.verify_size():
            return False
        sparse = self.is_sparse.get()
        group_name = self._internal_group_name()
        super_type = self.super_type.get()
        part_list = self.tl.selected.copy()
        delete_source_file = self.delete_source_file.get()
        attribute = self.attrib.get()
        block_device_name = self.block_device_name.get()
        self.destroy()
        self._start_animation()
        controller.start_pack(
            sparse=sparse,
            group_name=group_name,
            size=size,
            super_type=super_type,
            part_list=part_list,
            del_=delete_source_file,
            attrib=attribute,
            block_device_name=block_device_name,
            on_success=self._apply_pack_result,
            on_error=self._handle_pack_error,
            on_finally=self._stop_animation,
        )
        return None

    def _apply_pack_result(self, result):
        if result:
            output_path = result.output_path
            self._emit(
                self._texts.resolve_required_ui_text(
                    keys.PROJECT_PACK_SUPER_WINDOW_PACK_OUTPUT_SUCCESS_FORMAT
                )
                % output_path
            )
            if hasattr(result, "output_logical_size"):
                self._emit(describe_pack_super_result(result, texts=self._texts))
        else:
            self._show_error(
                self._texts.resolve_required_ui_text(keys.PACK_FAILED_MESSAGE)
            )

    def _handle_pack_error(self, exc: Exception):
        logging.exception("Pack super failed")
        self._show_error(
            f"{self._texts.resolve_required_ui_text(keys.PACK_FAILED_MESSAGE)}\n{exc}"
        )

    def verify_size(self):
        result = self._require_controller().validate_size(
            self.tl.selected, self.super_size.get()
        )
        if result.missing:
            missing = "\n".join(result.missing[:10])
            if len(result.missing) > 10:
                missing += f"\n... +{len(result.missing) - 10}"
            warn_win(
                texts=self._texts,
                text=self._texts.resolve_required_ui_text(
                    keys.IMAGE_MISSING_MESSAGE
                ).format(missing=missing),
                title=self._texts.resolve_required_ui_text(
                    keys.IMAGE_MISSING_DIALOG_TITLE
                ),
                ok=self._texts.resolve_required_ui_text(
                    keys.IMAGE_MISSING_DIALOG_OK_BUTTON
                ),
                master=self,
            )
            return False
        if not result.valid:
            self.super_size.set(result.suggested_size)
            ask_win(
                self._texts.resolve_required_ui_text(
                    keys.PROJECT_PACK_SUPER_WINDOW_PACK_SUPER_SIZE_TOO_SMALL
                ).format(self.super_size.get()),
                texts=self._texts,
                ok=self._texts.resolve_required_ui_text(
                    keys.SIZE_TOO_SMALL_CONFIRM_BUTTON
                ),
                cancel=self._texts.resolve_required_ui_text(
                    keys.SIZE_TOO_SMALL_CANCEL_BUTTON
                ),
                is_top=True,
                master=self,
            )
            return False
        return True

    def generate_async(self):
        self.generate_button.config(
            text=self._texts.resolve_required_ui_text(
                keys.PROJECT_PACK_SUPER_WINDOW_WORKING
            ),
            state="disabled",
        )
        self._require_controller().generate_dynamic_list(
            group_name=self._internal_group_name(),
            size=self.super_size.get(),
            super_type=self.super_type.get(),
            part_list=self.tl.selected.copy(),
            on_error=self._handle_generate_error,
            on_finally=self._finalize_generate,
        )

    def _handle_generate_error(self, exc: Exception):
        logging.exception("Generate super dynamic list failed")
        warn_win(
            texts=self._texts,
            text=str(exc),
            title=self._texts.resolve_required_ui_text(
                keys.GENERATE_FAILED_DIALOG_TITLE
            ),
            ok=self._texts.resolve_required_ui_text(
                keys.GENERATE_FAILED_DIALOG_OK_BUTTON
            ),
            master=self,
        )

    def _finalize_generate(self):
        if self.winfo_exists():
            self.generate_button.config(
                text=self._texts.resolve_required_ui_text(
                    keys.PROJECT_PACK_SUPER_WINDOW_GENERATE_LIST
                ),
                state="normal",
            )

    def refresh(self):
        self.tl.clear()
        for entry in self._require_controller().scan_images(self.selected):
            self.tl.insert(
                format_packable_super_image(entry, texts=self._texts),
                entry.name,
                entry.selected,
            )

    def read_list(self):
        state = self._require_controller().load_initial_state()
        if state.block_device_name:
            self.block_device_name.set(state.block_device_name)
        if isinstance(state.super_size, int):
            self.super_size.set(state.super_size)
        if state.group_name:
            self.group_name.set(self._display_group_name(state.group_name))
        if isinstance(state.super_type, int):
            self.super_type.set(state.super_type)
        self.selected = list(state.selected)


__all__ = ["PackSuper"]
