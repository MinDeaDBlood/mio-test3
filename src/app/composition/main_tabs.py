from __future__ import annotations

import sys
from pathlib import Path

from src.app.localization import ensure_selected_language_loaded
from src.app.localization_runtime import lang
from src.app.pro_runtime import is_pro
from src.app.runtime.contexts.settings import resolve_settings, resolve_states
from src.platform.system_shell import open_external_url
from src.core.paths import prog_path
from src.ui.assets.loader import load_photo_image
from src.ui.tabs.about.presenter import AboutTabPresenter
from src.ui.tabs.about.view import build_about_tab
from src.ui.tabs.home.assets import HOME_PHOTO_PATH_PARTS, HOME_PHOTO_SIZE
from src.ui.tabs.home.view import build_home_tab
from src.ui.tabs.tools.view import build_tools_tab


def _build_tool_openers():
    from src.app.composition.allow_selinux_audit import open_allow_selinux_audit_window
    from src.app.composition.byte_calculator import open_byte_calculator_window
    from src.app.composition.decrypt_xtc_xml import open_decrypt_xtc_xml_window
    from src.app.composition.disable_avb import open_disable_avb_window
    from src.app.composition.disable_encryption import open_disable_encryption_window
    from src.app.composition.download_firmware import open_firmware_download
    from src.app.composition.get_file_info import open_get_file_info_window
    from src.app.composition.magisk_patch import open_magisk_patch_window
    from src.app.composition.merge_qualcomm_image import (
        open_merge_qualcomm_image_window,
    )
    from src.app.composition.merge_super import open_merge_super_window
    from src.app.composition.mtk_port_tool import open_mtk_port_tool_window
    from src.app.composition.split_super import open_split_super_window
    from src.app.composition.trim_raw_image import open_trim_raw_image_window

    return {
        "download_firmware": open_firmware_download,
        "get_file_info": open_get_file_info_window,
        "byte_calculator": open_byte_calculator_window,
        "allow_selinux_audit": open_allow_selinux_audit_window,
        "disable_avb": open_disable_avb_window,
        "disable_encryption": open_disable_encryption_window,
        "trim_raw_image": open_trim_raw_image_window,
        "magisk_patch": open_magisk_patch_window,
        "merge_qualcomm_image": open_merge_qualcomm_image_window,
        "merge_super": open_merge_super_window,
        "split_super": open_split_super_window,
        "decrypt_xtc_xml": open_decrypt_xtc_xml_window,
        "mtk_port_tool": open_mtk_port_tool_window,
    }


def _home_photo_path() -> Path:
    return Path(prog_path).joinpath(*HOME_PHOTO_PATH_PARTS)


def compose_main_tabs(window) -> None:
    settings = resolve_settings()
    states = resolve_states()
    welcome_image = load_photo_image(_home_photo_path(), size=HOME_PHOTO_SIZE)

    def debugger_is_open() -> bool:
        return bool(states.debugger_window)

    def open_debugger() -> None:
        from src.app.composition.debugger import open_debugger_window

        debugger = open_debugger_window()
        states.debugger_window = bool(debugger.winfo_exists())
        debugger.lift()
        debugger.focus_force()
        debugger.wait_window()
        states.debugger_window = False

    build_about_tab(
        window,
        presenter=AboutTabPresenter(
            texts=lang, settings_obj=settings, py_version=sys.version
        ),
        debugger_is_open=debugger_is_open,
        open_debugger=open_debugger,
        open_repository=lambda: open_external_url(
            "https://github.com/ColdWindScholar/MIO-KITCHEN-SOURCE"
        ),
        is_pro_mode=is_pro,
    )
    build_tools_tab(
        window,
        openers=_build_tool_openers(),
        texts=lang,
        ensure_texts_loaded=ensure_selected_language_loaded,
    )
    build_home_tab(window, image=welcome_image, texts=lang)


__all__ = ["compose_main_tabs"]
