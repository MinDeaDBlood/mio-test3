import logging
import time
import tkinter as tk
from tkinter import (
    BOTH,
    BOTTOM,
    LEFT,
    TOP,
    X,
    BooleanVar,
    Frame,
    IntVar,
    Label,
    StringVar,
)
from tkinter import ttk

from src.ui.localization import LocalizationCatalog
from src.ui.common.windowing import Toplevel
from src.ui.tabs.project.pack.registry import get_output_values
from src.ui.tabs.project.pack.partition.custom_size_dialog import edit_custom_ext4_sizes
from src.ui.tabs.project.pack.partition import keys


class PackPartition(Toplevel):
    def __init__(
        self,
        parts: list,
        *,
        texts: LocalizationCatalog,
        controller,
        host_window,
        auto_start: bool,
    ):
        self._texts = texts
        self.chosen_parts: list = parts
        self.custom_size = {}
        self._captured_form: dict[str, object] | None = None
        self.controller = controller
        self._auto_start = auto_start
        super().__init__()
        self.host_window = host_window
        self.spatchvb = IntVar(master=self)
        self.ext4_packer = StringVar(master=self, value="make_ext4fs")
        self.format = StringVar(master=self, value="raw")
        self.erofs_compress_format = StringVar(master=self, value="lz4hc")
        self.scale = IntVar(master=self, value=0)
        self.UTC = StringVar(master=self, value=str(int(time.time())))
        self.scale_erofs = IntVar(master=self)
        self.remove_source_files = IntVar(master=self)
        self.ext4_method = StringVar(
            master=self, value=self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_AUTOMATIC)
        )
        self.origin_fs = StringVar(master=self, value="ext")
        self.modify_fs = StringVar(master=self, value="ext")
        self.fs_conver = BooleanVar(master=self, value=False)
        self.erofs_old_kernel = BooleanVar(master=self, value=False)

        if self._auto_start:
            self.withdraw()
            self.after_idle(self._auto_start_pack)
            return

        self.title(self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_PACK_OPTIONS))
        lf1 = ttk.LabelFrame(
            self, text=self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_EXT4_OPTIONS)
        )
        lf1.pack(fill=BOTH, padx=5, pady=5)
        lf2 = ttk.LabelFrame(
            self, text=self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_EROFS_OPTIONS)
        )
        lf2.pack(fill=BOTH, padx=5, pady=5)
        lf3 = ttk.LabelFrame(
            self, text=self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_ADDITIONAL_SETTINGS)
        )
        lf3.pack(fill=BOTH, padx=5, pady=5)
        lf4 = ttk.LabelFrame(
            self, text=self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_PARTITIONS_TO_PACK)
        )
        lf4.pack(fill=BOTH, pady=5, padx=5)
        (sf1 := Frame(lf3)).pack(fill=X, padx=5, pady=5, side=TOP)
        # EXT4 Settings
        Label(lf1, text=self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_PACKER_LABEL)).pack(
            side="left", padx=5, pady=5
        )
        ttk.Combobox(
            lf1,
            state="readonly",
            values=("make_ext4fs", "mke2fs+e2fsdroid"),
            textvariable=self.ext4_packer,
        ).pack(side="left", padx=5, pady=5)
        Label(
            lf1, text=self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_IMAGE_SIZE_LABEL)
        ).pack(side="left", padx=5, pady=5)
        ttk.Combobox(
            lf1,
            state="readonly",
            values=(
                self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_AUTOMATIC),
                self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_SAME_AS_ORIGINAL),
            ),
            textvariable=self.ext4_method,
        ).pack(side="left", padx=5, pady=5)
        self.modify_size_button = ttk.Button(
            lf1,
            text=self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_MODIFY_SIZE),
            command=self.modify_custom_size,
        )
        self.modify_size_button.pack(side="left", padx=5, pady=5)
        self.show_modify_size = (
            lambda: self.modify_size_button.pack_forget()
            if self.ext4_method.get()
            == self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_AUTOMATIC)
            else self.modify_size_button.pack(side="left", padx=5, pady=5)
        )
        self.ext4_method.trace("w", lambda *x: self.show_modify_size())
        self.show_modify_size()
        #
        Label(
            lf3, text=self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_OUTPUT_FORMAT_LABEL)
        ).pack(side="left", padx=5, pady=5)
        ttk.Combobox(
            lf3, state="readonly", textvariable=self.format, values=get_output_values()
        ).pack(padx=5, pady=5, side="left")
        Label(
            lf2, text=self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_COMPRESSION_METHOD)
        ).pack(side="left", padx=5, pady=5)
        ttk.Combobox(
            lf2,
            state="readonly",
            textvariable=self.erofs_compress_format,
            values=("lz4", "lz4hc", "lzma", "deflate", "zstd"),
        ).pack(side="left", padx=5, pady=5)
        ttk.Checkbutton(
            lf2,
            text=self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_OLD_KERNEL_SUPPORT),
            variable=self.erofs_old_kernel,
            onvalue=True,
            offvalue=False,
            style="Switch.TCheckbutton",
        ).pack(padx=5, pady=5, fill=BOTH)
        # --
        scales_erofs = ttk.Scale(
            lf2,
            from_=0,
            to=9,
            orient="horizontal",
            command=lambda x: self.label_e.config(
                text=self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_EROFS_LEVEL_FORMAT).format(
                    int(float(x))
                )
            ),
            variable=self.scale_erofs,
        )
        self.label_e = tk.Label(
            lf2,
            text=self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_EROFS_LEVEL_FORMAT).format(
                int(scales_erofs.get())
            ),
        )
        self.label_e.pack(side="left", padx=5, pady=5)
        scales_erofs.pack(fill="x", padx=5, pady=5)
        # --
        scales = ttk.Scale(
            sf1,
            from_=0,
            to=9,
            orient="horizontal",
            command=lambda x: self.label.config(
                text=self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_COMPRESSION_LEVEL_FORMAT).format(
                    int(float(x))
                )
                % self._texts.resolve_required_ui_text(keys.BROTLI_NAME)
            ),
            variable=self.scale,
        )
        self.label = ttk.Label(
            sf1,
            text=self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_COMPRESSION_LEVEL_FORMAT).format(
                int(scales.get())
            )
            % self._texts.resolve_required_ui_text(keys.BROTLI_NAME),
        )
        self.label.pack(side="left", padx=5, pady=5)
        scales.pack(fill="x", padx=5, pady=5)
        f = Frame(lf3)
        ttk.Label(f, text=self._texts.resolve_required_ui_text(keys.UTC_LABEL)).pack(
            side=LEFT, fill=X, padx=5, pady=5
        )
        ttk.Entry(f, textvariable=self.UTC).pack(side=LEFT, fill=X, padx=5, pady=5)
        f.pack(fill=X, padx=5, pady=5)

        frame_t = Frame(lf3)
        ttk.Checkbutton(
            frame_t,
            text=self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_PATCH_VBMETA),
            variable=self.spatchvb,
            onvalue=1,
            offvalue=0,
            style="Switch.TCheckbutton",
        ).pack(padx=5, pady=5, fill=X, side=LEFT)
        ttk.Checkbutton(
            frame_t,
            text=self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_REMOVE_ORIGINAL_FILE),
            variable=self.remove_source_files,
            onvalue=1,
            offvalue=0,
            style="Switch.TCheckbutton",
        ).pack(padx=5, pady=5, fill=X, side=LEFT)
        frame_t.pack(fill=X, padx=5, pady=5, side=BOTTOM)
        ttk.Checkbutton(
            lf3,
            text=self._texts.resolve_required_ui_text(keys.FS_CONVERTER_CHECKBOX),
            variable=self.fs_conver,
            onvalue=True,
            offvalue=False,
            style="Switch.TCheckbutton",
        ).pack(padx=5, pady=5, fill=BOTH)
        fs_conver = ttk.Frame(lf3, width=20)
        ttk.Combobox(
            fs_conver,
            textvariable=self.origin_fs,
            values=("ext", "f2fs", "erofs"),
            width=6,
            state="readonly",
        ).pack(padx=2, pady=2, fill=X, side=LEFT)
        ttk.Label(
            fs_conver, text=self._texts.resolve_required_ui_text(keys.FS_CONVERT_ARROW)
        ).pack(side=LEFT, fill=X, padx=1, pady=1)
        ttk.Combobox(
            fs_conver,
            textvariable=self.modify_fs,
            values=("ext", "f2fs", "erofs"),
            width=6,
            state="readonly",
        ).pack(padx=2, pady=2, fill=X, side=LEFT)
        self.fs_conver.trace(
            "w",
            lambda *z: fs_conver.pack_forget()
            if not self.fs_conver.get()
            else fs_conver.pack(padx=5, pady=5, fill=X),
        )

        ttk.Button(
            self,
            text=self._texts.resolve_required_ui_text(keys.CANCEL_BUTTON),
            command=self.destroy,
        ).pack(side="left", padx=2, pady=2, fill=X, expand=True)
        ttk.Button(
            self,
            text=self._texts.resolve_required_ui_text(keys.PACK_BUTTON),
            command=self.start_async,
            style="Accent.TButton",
        ).pack(side="left", padx=2, pady=2, fill=X, expand=True)
        self.center_on_screen(force=True)
        self.controller.notify_before_pack()

    def _capture_form(self) -> dict[str, object]:
        form = self._collect_form_values()
        self._captured_form = form
        return form

    def _auto_start_pack(self):
        try:
            self._capture_form()
            self.start_()
        finally:
            try:
                self.destroy()
            except Exception:
                logging.exception("PackPartition auto-start cleanup failed")

    def start_(self):
        return self.packrom()

    def start_async(self):
        if not self.controller.project_exists():
            self.host_window.message_pop(
                self._texts.resolve_required_ui_text(
                    keys.START_PROJECT_REQUIRED_MESSAGE
                ),
                "red",
            )
            return False
        form = self._capture_form()
        try:
            self.controller.validate_form(form)
        except ValueError as exc:
            self.host_window.message_pop(
                self._texts.resolve_optional(str(exc), default=str(exc)), "red"
            )
            return False
        self._captured_form = None
        self.destroy()
        self.controller.execute_background(form)
        return None

    def modify_custom_size(self):
        initial_sizes = self.controller.load_fixed_sizes(
            chosen_parts=self.chosen_parts,
            custom_size=self.custom_size,
        )
        edit_custom_ext4_sizes(
            texts=self._texts,
            chosen_parts=self.chosen_parts,
            custom_size=self.custom_size,
            initial_sizes=initial_sizes,
        )

    def _collect_form_values(self) -> dict[str, object]:
        return {
            "chosen_parts": list(self.chosen_parts),
            "patch_vbmeta": self.spatchvb.get() == 1,
            "remove_source_files": self.remove_source_files.get() == 1,
            "ext4_packer": self.ext4_packer.get(),
            "ext4_size_mode": "fixed"
            if self.ext4_method.get()
            == self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_SAME_AS_ORIGINAL)
            else "auto",
            "output_format": self.format.get(),
            "erofs_compress_format": self.erofs_compress_format.get(),
            "erofs_level": int(self.scale_erofs.get()),
            "brotli_level": int(self.scale.get()),
            "utc": str(self.UTC.get()).strip(),
            "origin_fs": self.origin_fs.get(),
            "modify_fs": self.modify_fs.get(),
            "fs_convert": self.fs_conver.get(),
            "erofs_old_kernel": self.erofs_old_kernel.get(),
            "custom_size": dict(self.custom_size),
        }

    def packrom(self) -> bool | None:
        if not self.controller.project_exists():
            self.host_window.message_pop(
                self._texts.resolve_required_ui_text(
                    keys.PACK_PROJECT_REQUIRED_MESSAGE
                ),
                "red",
            )
            return False
        form = self._captured_form or self._collect_form_values()
        self._captured_form = None
        try:
            self.controller.validate_form(form)
        except ValueError as exc:
            self.host_window.message_pop(
                self._texts.resolve_optional(str(exc), default=str(exc)), "red"
            )
            return False
        self.controller.execute_background(form)
        return None
