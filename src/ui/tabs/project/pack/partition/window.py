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
from src.ui.common.windowing import Toplevel, present_window
from src.ui.common.technical_choices import build_choice_set
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
    ):
        self._texts = texts
        self.chosen_parts: list = parts
        self.custom_size = {}
        self.controller = controller
        self.host_window = host_window
        super().__init__(master=host_window)
        self.spatchvb = IntVar(master=self)
        self._ext4_packer_choices = build_choice_set(
            self._texts, ("make_ext4fs", "mke2fs+e2fsdroid")
        )
        self._output_format_choices = build_choice_set(
            self._texts, get_output_values()
        )
        self._erofs_compression_choices = build_choice_set(
            self._texts, ("lz4", "lz4hc", "lzma", "deflate", "zstd")
        )
        self._filesystem_choices = build_choice_set(
            self._texts, ("ext", "f2fs", "erofs")
        )
        self.ext4_packer = StringVar(
            master=self, value=self._ext4_packer_choices.label_for("make_ext4fs")
        )
        self.format = StringVar(
            master=self, value=self._output_format_choices.label_for("raw")
        )
        self.erofs_compress_format = StringVar(
            master=self, value=self._erofs_compression_choices.label_for("lz4hc")
        )
        self.scale = IntVar(master=self, value=0)
        self.UTC = StringVar(master=self, value=str(int(time.time())))
        self.scale_erofs = IntVar(master=self)
        self.remove_source_files = IntVar(master=self)
        self.ext4_method = StringVar(
            master=self, value=self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_AUTOMATIC)
        )
        self.origin_fs = StringVar(
            master=self, value=self._filesystem_choices.label_for("ext")
        )
        self.modify_fs = StringVar(
            master=self, value=self._filesystem_choices.label_for("ext")
        )
        self.fs_conver = BooleanVar(master=self, value=False)
        self.erofs_old_kernel = BooleanVar(master=self, value=False)


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
        self.ext4_packer_box = ttk.Combobox(
            lf1,
            state="readonly",
            values=self._ext4_packer_choices.labels,
            textvariable=self.ext4_packer,
        )
        self.ext4_packer_box.current(
            self._ext4_packer_choices.index_for("make_ext4fs")
        )
        self.ext4_packer_box.pack(side="left", padx=5, pady=5)
        Label(
            lf1, text=self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_IMAGE_SIZE_LABEL)
        ).pack(side="left", padx=5, pady=5)
        self.ext4_size_mode_box = ttk.Combobox(
            lf1,
            state="readonly",
            values=(
                self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_AUTOMATIC),
                self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_SAME_AS_ORIGINAL),
            ),
            textvariable=self.ext4_method,
        )
        self.ext4_size_mode_box.current(0)
        self.ext4_size_mode_box.pack(side="left", padx=5, pady=5)
        self.modify_size_button = ttk.Button(
            lf1,
            text=self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_MODIFY_SIZE),
            command=self.modify_custom_size,
        )
        self.modify_size_button.pack(side="left", padx=5, pady=5)
        self.show_modify_size = (
            lambda: self.modify_size_button.pack_forget()
            if self.ext4_size_mode_box.current() == 0
            else self.modify_size_button.pack(side="left", padx=5, pady=5)
        )
        self.ext4_method.trace("w", lambda *x: self.show_modify_size())
        self.show_modify_size()
        #
        Label(
            lf3, text=self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_OUTPUT_FORMAT_LABEL)
        ).pack(side="left", padx=5, pady=5)
        self.output_format_box = ttk.Combobox(
            lf3,
            state="readonly",
            textvariable=self.format,
            values=self._output_format_choices.labels,
        )
        self.output_format_box.current(self._output_format_choices.index_for("raw"))
        self.output_format_box.pack(padx=5, pady=5, side="left")
        Label(
            lf2, text=self._texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_WINDOW_COMPRESSION_METHOD)
        ).pack(side="left", padx=5, pady=5)
        self.erofs_compression_box = ttk.Combobox(
            lf2,
            state="readonly",
            textvariable=self.erofs_compress_format,
            values=self._erofs_compression_choices.labels,
        )
        self.erofs_compression_box.current(
            self._erofs_compression_choices.index_for("lz4hc")
        )
        self.erofs_compression_box.pack(side="left", padx=5, pady=5)
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
        self.origin_fs_box = ttk.Combobox(
            fs_conver,
            textvariable=self.origin_fs,
            values=self._filesystem_choices.labels,
            width=6,
            state="readonly",
        )
        self.origin_fs_box.current(self._filesystem_choices.index_for("ext"))
        self.origin_fs_box.pack(padx=2, pady=2, fill=X, side=LEFT)
        ttk.Label(
            fs_conver, text=self._texts.resolve_required_ui_text(keys.FS_CONVERT_ARROW)
        ).pack(side=LEFT, fill=X, padx=1, pady=1)
        self.modify_fs_box = ttk.Combobox(
            fs_conver,
            textvariable=self.modify_fs,
            values=self._filesystem_choices.labels,
            width=6,
            state="readonly",
        )
        self.modify_fs_box.current(self._filesystem_choices.index_for("ext"))
        self.modify_fs_box.pack(padx=2, pady=2, fill=X, side=LEFT)
        self.fs_conver.trace(
            "w",
            lambda *z: fs_conver.pack_forget()
            if not self.fs_conver.get()
            else fs_conver.pack(padx=5, pady=5, fill=X),
        )

        ttk.Button(
            self,
            text=self._texts.resolve_required_ui_text(keys.CANCEL_BUTTON),
            command=self.cancel,
        ).pack(side="left", padx=2, pady=2, fill=X, expand=True)
        ttk.Button(
            self,
            text=self._texts.resolve_required_ui_text(keys.PACK_BUTTON),
            command=self.start_async,
            style="Accent.TButton",
        ).pack(side="left", padx=2, pady=2, fill=X, expand=True)
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.center_on_screen(force=True)
        logging.getLogger(__name__).info(
            "partition_pack.options_opened: selected=%r",
            self.chosen_parts,
        )

    def cancel(self) -> None:
        logging.getLogger(__name__).info(
            "partition_pack.options_cancelled: selected=%r",
            self.chosen_parts,
        )
        self.destroy()
        present_window(self.host_window)

    def start_async(self):
        if not self.controller.project_exists():
            self.host_window.message_pop(
                self._texts.resolve_required_ui_text(
                    keys.START_PROJECT_REQUIRED_MESSAGE
                ),
                "red",
            )
            return False
        form = self._collect_form_values()
        try:
            self.controller.validate_form(form)
        except ValueError as exc:
            logging.getLogger(__name__).warning(
                "partition_pack.options_validation_failed: error=%s selected=%r",
                exc,
                self.chosen_parts,
            )
            self.host_window.message_pop(
                self._texts.resolve_optional(str(exc), default=str(exc)), "red"
            )
            return False
        logging.getLogger(__name__).info(
            "partition_pack.options_submitted: selected=%r output_format=%s "
            "ext4_packer=%s fs_convert=%s remove_source_files=%s patch_vbmeta=%s",
            self.chosen_parts,
            form["output_format"],
            form["ext4_packer"],
            form["fs_convert"],
            form["remove_source_files"],
            form["patch_vbmeta"],
        )
        self.destroy()
        present_window(self.host_window)
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
            "ext4_packer": self._ext4_packer_choices.value_at(
                self.ext4_packer_box.current()
            ),
            "ext4_size_mode": "fixed"
            if self.ext4_size_mode_box.current() == 1
            else "auto",
            "output_format": self._output_format_choices.value_at(
                self.output_format_box.current()
            ),
            "erofs_compress_format": self._erofs_compression_choices.value_at(
                self.erofs_compression_box.current()
            ),
            "erofs_level": int(self.scale_erofs.get()),
            "brotli_level": int(self.scale.get()),
            "utc": str(self.UTC.get()).strip(),
            "origin_fs": self._filesystem_choices.value_at(
                self.origin_fs_box.current()
            ),
            "modify_fs": self._filesystem_choices.value_at(
                self.modify_fs_box.current()
            ),
            "fs_convert": self.fs_conver.get(),
            "erofs_old_kernel": self.erofs_old_kernel.get(),
            "custom_size": dict(self.custom_size),
        }
