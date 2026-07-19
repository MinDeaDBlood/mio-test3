from __future__ import annotations

# Direct file execution bootstrap
import sys as _direct_sys
from pathlib import Path as _DirectPath

_DIRECT_PROJECT_ROOT = _DirectPath(__file__).resolve().parent
while _DIRECT_PROJECT_ROOT != _DIRECT_PROJECT_ROOT.parent:
    if (
        (_DIRECT_PROJECT_ROOT / "src").is_dir()
        and (_DIRECT_PROJECT_ROOT / "tests").is_dir()
        and (_DIRECT_PROJECT_ROOT / "scripts").is_dir()
    ):
        break
    _DIRECT_PROJECT_ROOT = _DIRECT_PROJECT_ROOT.parent
else:
    raise RuntimeError(f"Project root was not found for {__file__}")

_direct_root_text = str(_DIRECT_PROJECT_ROOT)
if _direct_root_text not in _direct_sys.path:
    _direct_sys.path.insert(0, _direct_root_text)
if __package__ in {None, ""}:
    _direct_relative = (
        _DirectPath(__file__)
        .resolve()
        .relative_to(_DIRECT_PROJECT_ROOT)
        .with_suffix("")
    )
    __package__ = ".".join(_direct_relative.parts[:-1])

import tkinter as tk
from collections.abc import Callable
from time import monotonic

from src.app.composition.allow_selinux_audit import open_allow_selinux_audit_window
from src.app.composition.boot_images import (
    open_boot_pack_window,
    open_boot_unpack_window,
)
from src.app.composition.byte_calculator import open_byte_calculator_window
from src.app.composition.convert import open_conversion_window
from src.app.composition.debugger import open_debugger_window
from src.app.composition.decrypt_xtc_xml import open_decrypt_xtc_xml_window
from src.app.composition.disable_avb import open_disable_avb_window
from src.app.composition.disable_encryption import open_disable_encryption_window
from src.app.composition.get_file_info import open_get_file_info_window
from src.app.composition.magisk_patch import open_magisk_patch_window
from src.app.composition.merge_qualcomm_image import (
    open_merge_qualcomm_image_window,
)
from src.app.composition.merge_super import open_merge_super_window
from src.app.composition.mtk_port_tool import open_mtk_port_tool_window
from src.app.composition.partition_pack import open_partition_pack
from src.app.composition.payload_pack import open_payload_pack_window
from src.app.composition.project_workspace import create_project_workspace
from src.app.composition.split_super import open_split_super_window
from src.app.composition.super_pack import open_super_pack_window
from src.app.composition.trim_raw_image import open_trim_raw_image_window
from src.app.composition.update import open_update_window
from src.app.runtime.contexts.settings import resolve_states
from src.ui.common.window_appearance import current_window_alpha
from src.ui.common.window_reveal import reveal_window_after_layout
from src.ui.tabs.project.pack.zip_prompt import prompt_hybrid_pack_option
from tests.support.runtime_smoke import lang, prepare_root
from tests.support.theme_assertions import cycle_light_dark


COVERED_TOPLEVEL_CLASSES = (
    "BootImagesPack",
    "BootImagesUnpack",
    "Debugger",
    "DecryptXtcXml",
    "FileBytes",
    "FormatConversion",
    "GetFileInfo",
    "MagiskPatcher",
    "MergeQualcommImageWindow",
    "MergeSparseImage",
    "MtkPortTool",
    "PackPartition",
    "PackSuper",
    "PayloadPackUnavailableWindow",
    "SelinuxAuditAllow",
    "SplitSuperWindow",
    "TrimImage",
    "UpdaterWindow",
)


def _native_state(window: tk.Misc) -> str:
    return str(window.tk.call("wm", "state", window._w))


def _wait_for_initial_show(name: str, window: tk.Toplevel, root: tk.Tk) -> None:
    deadline = monotonic() + 2.0
    while (
        window.winfo_exists()
        and not bool(getattr(window, "_initial_show_complete", False))
        and monotonic() < deadline
    ):
        root.update_idletasks()
        root.update()
    assert bool(getattr(window, "_initial_show_complete", False)), (
        f"{name} did not complete its first-paint reveal"
    )


def _assert_user_window(
    name: str,
    window: tk.Toplevel,
    root: tk.Tk,
    *,
    expected_owner: tk.Misc | None,
) -> None:
    _wait_for_initial_show(name, window, root)
    expected_owner_path = "" if expected_owner is None else str(expected_owner)
    assert str(window.transient()) == expected_owner_path, (
        f"{name} owner={window.transient()!r}, expected={expected_owner_path!r}"
    )
    assert _native_state(window) == "normal"
    assert window.winfo_viewable()
    cycle_light_dark(root, window)


def _open_and_close(
    name: str,
    opener: Callable[[], object],
    *,
    root: tk.Tk,
    expected_owner: tk.Misc | None,
) -> None:
    opened = opener()
    window = opened.window if hasattr(opened, "window") else opened
    if not isinstance(window, tk.Toplevel):
        raise AssertionError(f"{name} did not return a Toplevel window: {window!r}")
    _assert_user_window(name, window, root, expected_owner=expected_owner)
    window.destroy()
    root.update_idletasks()
    root.update()


root = prepare_root()
callback_errors: list[BaseException] = []
root.report_callback_exception = (
    lambda _kind, error, _traceback: callback_errors.append(error)
)
reveal_window_after_layout(root, target_alpha=current_window_alpha(), focus=True)

window_openers: tuple[tuple[str, Callable[[], object], tk.Misc | None], ...] = (
    ("get_file_info", open_get_file_info_window, None),
    ("merge_super", open_merge_super_window, None),
    ("magisk_patch", open_magisk_patch_window, None),
    ("disable_avb", open_disable_avb_window, None),
    ("disable_encryption", open_disable_encryption_window, None),
    ("allow_selinux_audit", open_allow_selinux_audit_window, None),
    # These composition functions explicitly pass the main window as master.
    ("boot_pack", open_boot_pack_window, root),
    ("boot_unpack", open_boot_unpack_window, root),
    ("byte_calculator", open_byte_calculator_window, None),
    ("decrypt_xtc_xml", open_decrypt_xtc_xml_window, None),
    ("merge_qualcomm", open_merge_qualcomm_image_window, None),
    ("mtk_port", open_mtk_port_tool_window, None),
    ("split_super", open_split_super_window, None),
    ("trim_raw_image", open_trim_raw_image_window, None),
    ("payload_pack", open_payload_pack_window, None),
    ("debugger", open_debugger_window, None),
    ("conversion", lambda: open_conversion_window(master=root), root),
    ("super_pack", open_super_pack_window, root),
    ("partition_pack", lambda: open_partition_pack(["system"]), root),
    ("updater", lambda: open_update_window(auto_start=False), None),
)

for window_name, open_window, expected_owner in window_openers:
    _open_and_close(
        window_name,
        open_window,
        root=root,
        expected_owner=expected_owner,
    )
    if window_name == "updater":
        resolve_states().update_window = False

zip_window_states: list[str] = []
zip_transient_owners: list[str] = []


def close_zip_window() -> None:
    for child in root.winfo_children():
        if not isinstance(child, tk.Toplevel) or not child.winfo_exists():
            continue
        if child.title() != lang.resolve_required_ui_text(
            "project_pack_zip_prompt_pack_zip"
        ):
            continue
        if not bool(getattr(child, "_initial_show_complete", False)):
            root.after(10, close_zip_window)
            return
        zip_window_states.append(_native_state(child))
        zip_transient_owners.append(str(child.transient()))
        child.destroy()
        return
    root.after(20, close_zip_window)


root.after(50, close_zip_window)
assert prompt_hybrid_pack_option(root, texts=lang) is None
assert zip_window_states == ["normal"]
assert zip_transient_owners == [str(root)]

workspace = create_project_workspace(host_window=root)
unpack_view = workspace["unpack_view"]
unpack_view.update_idletasks()
root.update()

assert callback_errors == []
root.destroy()
print(f"WINDOW_SMOKE_OK: checked={len(window_openers) + 1}")

if __name__ == "__main__":
    from tests.support.direct_execution import support_module_main

    raise SystemExit(support_module_main(__file__))
