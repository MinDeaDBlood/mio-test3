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

import tempfile
import tkinter as tk
from pathlib import Path
from time import monotonic

from src.app.file_dialog_paths import DialogTarget, DialogTargetKind
from src.logic.plugins.config.service import PluginConfigInfo, PluginDialogConfig
from src.logic.plugins.editor.service import PluginEditorTarget
from src.logic.plugins.models import ModuleErrorCodes
from src.logic.plugins.package_reader import PluginPackageInfo
from src.logic.projects.pack.postinstall import PostInstallEntry
from src.ui.common.controls import input_
from src.ui.common.window_appearance import current_window_alpha
from src.ui.common.window_reveal import reveal_window_after_layout
from src.ui.common.dialogs.error_helper import show_error_helper
from src.ui.common.mkc_filedialog import DirectorySelectionDialog, FileSelectionDialog
from src.ui.tabs.plugins.installer.window import PluginInstallerWindow
from src.ui.tabs.plugins.plugin_config_dialog import PluginConfigDialog
from src.ui.tabs.plugins.plugin_new_dialog import PluginNewDialog
from src.ui.tabs.plugins.plugin_uninstall_dialog import PluginUninstallDialog
from src.ui.tabs.plugins.store.dialogs import prompt_repository_url
from src.ui.tabs.plugins.store.window import MpkStore
from src.ui.tabs.project.pack.partition.custom_size_dialog import edit_custom_ext4_sizes
from src.ui.tabs.project.pack.postinstall.editor_window import (
    PostInstallConfigEditorWindow,
)
from src.ui.tabs.project.unpack.info_dialog import show_unpack_image_info_dialog
from src.ui.tabs.tools.fstab_patch_window import FstabPatchWindow
from src.ui.tabs.tools.mtk_port_tool.panel import FileChooser
from src.ui.warn.dialogs import ask_win, info_win, warn_win
from tests.support.runtime_smoke import lang, prepare_root
from tests.support.theme_assertions import cycle_light_dark


COVERED_TOPLEVEL_CLASSES = (
    "DirectorySelectionDialog",
    "FileChooser",
    "FileSelectionDialog",
    "FstabPatchWindow",
    "PluginInstallerWindow",
    "MpkStore",
    "PluginConfigDialog",
    "PluginNewDialog",
    "PluginUninstallDialog",
    "PostInstallConfigEditorWindow",
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


def _assert_and_close(
    name: str,
    window: tk.Toplevel,
    root: tk.Tk,
    *,
    expected_owner: tk.Misc | None = None,
) -> None:
    _wait_for_initial_show(name, window, root)
    assert window.winfo_exists(), f"{name} was destroyed during creation"
    assert _native_state(window) == "normal", f"{name} state={_native_state(window)}"
    assert window.winfo_viewable(), f"{name} is not viewable"
    expected_owner_path = "" if expected_owner is None else str(expected_owner)
    assert str(window.transient()) == expected_owner_path, (
        f"{name} owner={window.transient()!r}, expected={expected_owner_path!r}"
    )
    cycle_light_dark(root, window)
    window.destroy()
    root.update_idletasks()
    root.update()


def _modal_snapshot_and_close(root: tk.Tk, snapshots: list[tuple[str, str]]) -> None:
    for child in root.winfo_children():
        if not isinstance(child, tk.Toplevel) or not child.winfo_exists():
            continue
        if not bool(getattr(child, "_initial_show_complete", False)):
            root.after(10, _modal_snapshot_and_close, root, snapshots)
            return
        snapshots.append((_native_state(child), str(child.transient())))
        child.destroy()
        return
    root.after(20, _modal_snapshot_and_close, root, snapshots)


class _NewPluginController:
    def create_plugin(self, data):
        return str(data.get("id") or "demo.plugin")

    def prepare_editor_target(self, plugin_id):
        return PluginEditorTarget(Path(tempfile.gettempdir()), plugin_id, True)


class _UninstallController:
    def is_installed(self, _plugin_id):
        return False

    def is_virtual(self, _plugin_id):
        return False

    def get_name(self, plugin_id):
        return plugin_id

    def collect_dependent_plugin_ids(self, _plugin_id):
        return []


class _PostInstallController:
    def load(self):
        return {}

    def create_entry(self, partition, **values):
        return PostInstallEntry(partition=partition, **values)

    def normalize_partition_name(self, value):
        return str(value).strip()

    def save(self, _entries):
        return None


class _InstallerController:
    def __init__(self) -> None:
        self.notified = False

    def read_package(self, _path):
        return PluginPackageInfo(
            path=Path(_path),
            name="Demo plugin",
            version="1.0",
            author="MIO",
            description="Smoke package",
            icon_data=None,
        )

    def install(self, _path, *, on_success, on_error):
        del on_error
        on_success((0, ""))

    def notify_catalog_changed(self):
        self.notified = True


class _ConfigService:
    def load(self, _path):
        return PluginDialogConfig(
            info=PluginConfigInfo(
                title="Plugin configuration",
                height="None",
                width="None",
                resize=False,
                assert_unknown_control=False,
            ),
            groups=(),
        )

    def execute_command(self, _command, _context):
        return None


root = prepare_root()
callback_errors: list[BaseException] = []
root.report_callback_exception = (
    lambda _kind, error, _traceback: callback_errors.append(error)
)
reveal_window_after_layout(root, target_alpha=current_window_alpha(), focus=True)

opened = 0

file_dialog = FileSelectionDialog(
    texts=lang,
    title="File selection",
    filetypes=(("All", "*"),),
    initial_directory="/tmp",
    resolve_activation=lambda _path, _name: DialogTarget(
        DialogTargetKind.SELECT,
        "/tmp/selected",
    ),
    accept_target=lambda _path, _name: "/tmp/selected",
    refresh_files=lambda *_args, **_kwargs: None,
    show_error=lambda _message: None,
)
_assert_and_close("FileSelectionDialog", file_dialog, root)
opened += 1

directory_dialog = DirectorySelectionDialog(
    texts=lang,
    title="Directory selection",
    initial_directory="/tmp",
    resolve_activation=lambda _path, _name: DialogTarget(
        DialogTargetKind.NAVIGATE,
        "/tmp",
    ),
    accept_target=lambda _path, _name: "/tmp",
    refresh_directories=lambda *_args, **_kwargs: None,
    show_error=lambda _message: None,
)
_assert_and_close("DirectorySelectionDialog", directory_dialog, root)
opened += 1

plugin_store = MpkStore(texts=lang)
plugin_store.deiconify()
_assert_and_close("MpkStore", plugin_store, root)
opened += 1

new_plugin = PluginNewDialog(
    _NewPluginController(),
    texts=lang,
    open_editor=lambda _target: None,
    show_info=lambda _message: None,
)
_assert_and_close("PluginNewDialog", new_plugin, root)
opened += 1

uninstall = PluginUninstallDialog(
    _UninstallController(),
    "",
    texts=lang,
    show_message=lambda *_args, **_kwargs: None,
)
_assert_and_close("PluginUninstallDialog", uninstall, root)
opened += 1

fstab = FstabPatchWindow(
    texts=lang,
    title="Fstab patch",
    info_text="Information",
    available_partitions_text="Partitions",
    select_all_text="Select all",
    refresh_text="Refresh",
    run_text="Run",
    running_text="Running",
    no_partitions_text="No partitions",
    selection_warning="Select a partition",
    completion_message=lambda count: f"Completed: {count}",
    warning_dialog_title="Warning",
    warning_dialog_ok="OK",
    completion_dialog_title="Complete",
    completion_dialog_ok="OK",
)
_assert_and_close("FstabPatchWindow", fstab, root)
opened += 1

postinstall = PostInstallConfigEditorWindow(
    texts=lang,
    controller=_PostInstallController(),
    show_error=lambda _message: None,
)
_assert_and_close("PostInstallConfigEditorWindow", postinstall, root)
opened += 1

file_chooser = FileChooser(
    root,
    texts=lang,
    initial_directory="/tmp",
)
_assert_and_close("FileChooser", file_chooser, root, expected_owner=root)
opened += 1

info_dialog = show_unpack_image_info_dialog(
    texts=lang,
    info_rows=(("filesystem", "ext4"),),
)
_assert_and_close("UnpackInfoDialog", info_dialog, root)
opened += 1

show_error_helper(
    texts=lang,
    source_text="source",
    detail="detail",
    solution="solution",
    confidence=90,
    ok_text="OK",
)
root.update_idletasks()
root.update()
error_helper = next(
    child for child in root.winfo_children() if isinstance(child, tk.Toplevel)
)
_assert_and_close("ErrorHelper", error_helper, root)
opened += 1

config_snapshots: list[tuple[str, str]] = []
root.after(40, _modal_snapshot_and_close, root, config_snapshots)
PluginConfigDialog(
    "ignored.json",
    texts=lang,
    config_service=_ConfigService(),
    choose_file=lambda: "",
    show_error=lambda _message: None,
)
assert config_snapshots == [("normal", "")]
opened += 1

repository_dialog = prompt_repository_url(
    parent=root,
    current_value="https://example.invalid/plugins/",
    title="Repository",
    ok_text="OK",
    cancel_text="Cancel",
    move_center=lambda window: window.center_on_screen(force=True),
    on_accept=lambda _value: None,
)
_assert_and_close(
    "PluginRepositoryDialog",
    repository_dialog,
    root,
    expected_owner=root,
)
opened += 1

custom_size_snapshots: list[tuple[str, str]] = []
root.after(40, _modal_snapshot_and_close, root, custom_size_snapshots)
edit_custom_ext4_sizes(
    texts=lang,
    chosen_parts=("system",),
    custom_size={},
    initial_sizes={"system": 1024},
)
assert custom_size_snapshots == [("normal", "")]
opened += 1

for dialog_name, callback in (
    (
        "WarningDialog",
        lambda: warn_win(texts=lang, text="warning", master=root),
    ),
    (
        "InformationDialog",
        lambda: info_win("information", texts=lang, master=root),
    ),
    (
        "ConfirmationDialog",
        lambda: ask_win("confirm", texts=lang, master=root, is_top=True, wait=True),
    ),
):
    snapshots: list[tuple[str, str]] = []
    root.after(40, _modal_snapshot_and_close, root, snapshots)
    callback()
    assert snapshots == [("normal", str(root))], dialog_name
    opened += 1

input_snapshots: list[tuple[str, str]] = []
root.after(40, _modal_snapshot_and_close, root, input_snapshots)
input_(texts=lang, title="Input", text="value")
assert input_snapshots == [("normal", "")]
opened += 1

installer_snapshots: list[tuple[str, str]] = []
installer_controller = _InstallerController()
root.after(40, _modal_snapshot_and_close, root, installer_snapshots)
PluginInstallerWindow(
    str(Path(tempfile.gettempdir()) / "demo.mpk"),
    texts=lang,
    controller=installer_controller,
    error_codes=ModuleErrorCodes,
)
assert installer_snapshots == [("normal", "")]
assert installer_controller.notified is True
opened += 1

assert callback_errors == []
root.destroy()
print(f"WINDOW_CATALOG_SMOKE_OK: checked={opened}")

if __name__ == "__main__":
    from tests.support.direct_execution import support_module_main

    raise SystemExit(support_module_main(__file__))
