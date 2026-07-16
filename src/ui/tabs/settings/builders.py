from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from tkinter import BOTH, X, StringVar, ttk

from src.ui.localization import LocalizationCatalog
from src.ui.tabs.settings.models import ToggleBinding
from src.ui.common.controls import ScrollFrame
from src.ui.common.widgets.toggled_frame import ToggledFrame


def _tr(texts: LocalizationCatalog, *keys: str) -> str:
    return texts.resolve(*keys, default="")


@dataclass(frozen=True)
class SettingsSections:
    scroll_frame: ScrollFrame
    main_toggle: ToggledFrame
    others_toggle: ToggledFrame
    theme_frame: ttk.Frame
    language_frame: ttk.Frame
    path_frame: ttk.Frame
    cache_frame: ttk.Frame
    update_frame: ttk.Frame
    others_frame: ttk.Frame


def build_settings_sections(window, *, texts: LocalizationCatalog) -> SettingsSections:
    scroll_frame = ScrollFrame(window.tab3)
    scroll_frame.gui()

    main_toggle = ToggledFrame(
        scroll_frame.label_frame,
        width=600,
        text=_tr(texts, "settings_builders_settings"),
        callback=scroll_frame.update_ui,
        unfold=True,
    )
    others_toggle = ToggledFrame(
        scroll_frame.label_frame,
        width=600,
        text=_tr(texts, "settings_builders_other"),
        callback=scroll_frame.update_ui,
    )

    return SettingsSections(
        scroll_frame=scroll_frame,
        main_toggle=main_toggle,
        others_toggle=others_toggle,
        theme_frame=ttk.Frame(main_toggle.sub_frame),
        language_frame=ttk.Frame(main_toggle.sub_frame),
        path_frame=ttk.Frame(main_toggle.sub_frame),
        cache_frame=ttk.Frame(main_toggle.sub_frame),
        update_frame=ttk.Frame(window.tab3),
        others_frame=others_toggle.sub_frame,
    )


def build_theme_section(
    master,
    *,
    texts: LocalizationCatalog,
    theme_var: StringVar,
    theme_choices: Iterable[str],
    on_selected: Callable[[], None],
):
    ttk.Label(master, text=_tr(texts, "settings_builders_theme_label")).pack(
        side="left", padx=10, pady=10
    )
    theme_box = ttk.Combobox(
        master, textvariable=theme_var, state="readonly", values=tuple(theme_choices)
    )
    theme_box.pack(padx=10, pady=10, side="left")
    theme_box.bind("<<ComboboxSelected>>", lambda *_args: on_selected())
    return theme_box


def build_path_section(
    master,
    *,
    texts: LocalizationCatalog,
    work_path_var,
    open_work_path: Callable[..., None],
    modpath: Callable[[], None],
):
    ttk.Label(
        master, text=_tr(texts, "settings_builders_working_directory_label")
    ).pack(side="left", padx=10, pady=10)
    work_path_label = ttk.Label(master, textvariable=work_path_var, wraplength=200)
    work_path_label.bind("<Button-1>", open_work_path)
    work_path_label.pack(padx=10, pady=10, side="left")
    ttk.Button(
        master, text=_tr(texts, "settings_builders_change"), command=modpath
    ).pack(side="left", padx=10, pady=10)
    return work_path_label


def build_language_section(
    master,
    *,
    texts: LocalizationCatalog,
    language_var: StringVar,
    languages: Iterable[str],
    on_selected: Callable[[], None],
):
    ttk.Label(master, text=_tr(texts, "settings_builders_language_select_label")).pack(
        side="left", padx=10, pady=10
    )
    language_box = ttk.Combobox(
        master, state="readonly", textvariable=language_var, values=tuple(languages)
    )
    language_box.pack(padx=10, pady=10, side="left")
    language_box.bind("<<ComboboxSelected>>", lambda *_args: on_selected())
    return language_box


def build_cache_section(
    master,
    *,
    texts: LocalizationCatalog,
    cache_text: str,
    open_cache_path: Callable[..., None],
    clear_cache_async: Callable[[], None],
):
    ttk.Label(master, text=_tr(texts, "cache_size")).pack(side="left", padx=10, pady=10)
    cache_label = ttk.Label(master, text=cache_text, wraplength=200)
    cache_label.bind("<Button-1>", open_cache_path)
    cache_label.pack(padx=10, pady=10, side="left")
    ttk.Button(
        master,
        text=_tr(texts, "settings_builders_clear_action"),
        command=clear_cache_async,
    ).pack(side="left", padx=10, pady=10)
    return cache_label


def build_toggle_button(master, *, item: ToggleBinding, variable: StringVar):
    ttk.Checkbutton(
        master,
        text=item.text,
        variable=variable,
        onvalue=item.on_value,
        offvalue=item.off_value,
        style=item.style,
    ).pack(padx=10, pady=10, fill=X)


def build_error_helper_section(
    master,
    *,
    texts: LocalizationCatalog,
    enabled_var: StringVar,
    confidence_var: StringVar,
    bind_enabled: Callable[[StringVar, str], None],
    on_confidence_changed: Callable[[str], None],
):
    bind_enabled(enabled_var, "error_helper_enabled")

    enabled_row = ttk.Frame(master)
    ttk.Label(enabled_row, text=_tr(texts, "error_helper_enabled")).pack(
        side="left", padx=10, pady=10
    )
    ttk.Checkbutton(
        enabled_row,
        variable=enabled_var,
        onvalue="1",
        offvalue="0",
        style="Switch.TCheckbutton",
    ).pack(side="left", padx=10, pady=10)
    enabled_row.pack(padx=10, pady=(0, 2), fill=X)

    row = ttk.Frame(master)
    ttk.Label(row, text=_tr(texts, "error_helper_confidence_label")).pack(
        side="left", padx=10, pady=10
    )
    value_var = StringVar(
        value=_tr(texts, "error_helper_confidence_value").format(
            value=confidence_var.get()
        )
    )

    initializing = {"active": True}

    def update_confidence(raw_value):
        value = str(int(round(float(raw_value))))
        confidence_var.set(value)
        value_var.set(_tr(texts, "error_helper_confidence_value").format(value=value))
        if not initializing["active"]:
            on_confidence_changed(value)

    scale = ttk.Scale(
        row, from_=50, to=100, orient="horizontal", command=update_confidence
    )
    try:
        scale.set(float(confidence_var.get()))
    except (TypeError, ValueError):
        scale.set(80)
    initializing["active"] = False
    scale.pack(side="left", padx=10, pady=10, fill=X, expand=True)
    ttk.Label(row, textvariable=value_var, width=6).pack(side="left", padx=10, pady=10)
    row.pack(padx=10, pady=(0, 10), fill=X)
    return scale


def build_other_toggles_section(
    master,
    *,
    texts: LocalizationCatalog,
    toggle_bindings: Iterable[ToggleBinding],
    bind_setting: Callable[[StringVar, str], None],
    context_var: StringVar,
    handle_context_patch: Callable[..., None],
):
    for item in toggle_bindings:
        var = StringVar(value=item.value)
        bind_setting(var, item.key)
        build_toggle_button(master, item=item, variable=var)

    enable_cp = ttk.Checkbutton(
        master,
        text=_tr(texts, "context_patch"),
        variable=context_var,
        onvalue="1",
        offvalue="0",
        style="Toggle.TButton",
    )
    enable_cp.pack(padx=10, pady=10, fill=X)
    context_var.trace_add("write", handle_context_patch)
    return enable_cp


def pack_settings_sections(sections: SettingsSections):
    for item in [
        sections.theme_frame,
        sections.language_frame,
        sections.path_frame,
        sections.cache_frame,
        sections.main_toggle,
        sections.others_toggle,
    ]:
        item.pack(padx=10, pady=7, fill="both")
    sections.scroll_frame.pack(fill=BOTH, expand=True)
    sections.update_frame.pack(padx=10, pady=(0, 10), fill=X)
    sections.scroll_frame.update_ui()


def build_update_section(
    master,
    *,
    texts: LocalizationCatalog,
    updater_func: Callable[[], None],
    check_upgrade_var: StringVar,
):
    check_frame = ttk.Frame(master)
    check_frame.columnconfigure(0, weight=1, uniform="update_actions")
    check_frame.columnconfigure(1, weight=1, uniform="update_actions")

    ttk.Button(
        check_frame,
        text=_tr(texts, "settings_builders_check_updates"),
        command=updater_func,
    ).grid(row=0, column=0, sticky="ew", padx=(10, 5), pady=8)

    auto_check_text = _tr(
        texts, "auto_check_updates", "settings_builders_check_updates"
    )
    ttk.Checkbutton(
        check_frame,
        text=auto_check_text,
        variable=check_upgrade_var,
        onvalue="1",
        offvalue="0",
    ).grid(row=0, column=1, sticky="ew", padx=(5, 10), pady=8)

    check_frame.pack(fill=X)
    return check_frame
