from __future__ import annotations

from tkinter import StringVar

from src.ui.localization import LocalizationCatalog
from src.ui.common.formatting import format_bytes
from src.ui.tabs.settings.models import build_toggle_bindings
from src.ui.tabs.settings.builders import (
    build_cache_section,
    build_language_section,
    build_error_helper_section,
    build_other_toggles_section,
    build_path_section,
    build_settings_sections,
    build_theme_section,
    build_update_section,
    pack_settings_sections,
)


def build_settings_tab(
    window,
    *,
    texts: LocalizationCatalog,
    runtime,
    controller,
    actions,
    task_runner,
    open_work_path,
    open_cache_path,
    confirm_context_patch,
):
    """Build settings widgets from already composed application dependencies."""

    def bind_setting(var: StringVar, key: str):
        var.trace_add("write", lambda *_: actions.apply_toggle(key, var.get()))

    def clear_cache_async():
        task_runner.run(
            controller.clear_cache,
            on_success=lambda size: cache_label.configure(text=format_bytes(size)),
            on_error=lambda exc: actions.report_error(
                "settings.cache.clear_failed", exc
            ),
        )

    def handle_context_patch(*_args):
        value, enabled = controller.handle_context_patch_toggle(
            desired_value=context_var.get(),
            confirm_enable=confirm_context_patch,
        )
        if value != context_var.get():
            context_var.set(value)
        enable_cp.configure(state="normal")

    window.show_local = StringVar(value=controller.get_work_path())
    sections = build_settings_sections(window, texts=texts)

    window.list2 = build_theme_section(
        sections.theme_frame,
        texts=texts,
        theme_var=runtime.theme_var,
        theme_choices=controller.get_theme_choices(),
        on_selected=actions.apply_theme,
    )

    build_path_section(
        sections.path_frame,
        texts=texts,
        work_path_var=window.show_local,
        open_work_path=open_work_path,
        modpath=actions.choose_and_apply_work_path,
    )

    build_language_section(
        sections.language_frame,
        texts=texts,
        language_var=runtime.language_var,
        languages=controller.list_available_languages(),
        on_selected=actions.apply_language,
    )

    cache_label = build_cache_section(
        sections.cache_frame,
        texts=texts,
        cache_text=format_bytes(controller.get_cache_size()),
        open_cache_path=open_cache_path,
        clear_cache_async=clear_cache_async,
    )

    error_helper_enabled_var = StringVar(
        value=runtime.settings_obj.error_helper_enabled
    )
    error_helper_confidence_var = StringVar(
        value=runtime.settings_obj.error_helper_confidence
    )
    build_error_helper_section(
        sections.others_frame,
        texts=texts,
        enabled_var=error_helper_enabled_var,
        confidence_var=error_helper_confidence_var,
        bind_enabled=bind_setting,
        on_confidence_changed=actions.apply_error_helper_confidence,
    )

    context_var = StringVar(value=runtime.settings_obj.contextpatch)
    check_upgrade_var = StringVar(value=runtime.settings_obj.check_upgrade)
    check_upgrade_var.trace_add(
        "write", lambda *_: actions.apply_auto_update(check_upgrade_var.get())
    )

    enable_cp = build_other_toggles_section(
        sections.others_frame,
        texts=texts,
        toggle_bindings=build_toggle_bindings(runtime.settings_obj, texts),
        bind_setting=bind_setting,
        context_var=context_var,
        handle_context_patch=handle_context_patch,
    )

    build_update_section(
        sections.update_frame,
        texts=texts,
        updater_func=actions.open_updater,
        check_upgrade_var=check_upgrade_var,
    )
    pack_settings_sections(sections)


__all__ = ["build_settings_tab"]
