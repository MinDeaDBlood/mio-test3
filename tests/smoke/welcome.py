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
    _direct_relative = _DirectPath(__file__).resolve().relative_to(
        _DIRECT_PROJECT_ROOT
    ).with_suffix("")
    __package__ = ".".join(_direct_relative.parts[:-1])


from dataclasses import dataclass
import tkinter as tk
from time import monotonic

from src.app.composition.main_window import compose_main_window, create_main_window
from src.app.composition.window_runtime import initialize_window_runtime
from src.app.localization import load_language_from_files
from src.app.localization_runtime import lang
from src.app.runtime.session import ensure_runtime_session

from src.app.welcome.actions import WelcomeActions
from src.ui.common.window_appearance import current_window_alpha
from src.ui.common.window_reveal import reveal_window_after_layout
from src.ui.welcome.wizard import Welcome


@dataclass(frozen=True)
class _MainData:
    languages: tuple[str, ...] = ("English", "Russian")
    selected_language: str = "English"


@dataclass(frozen=True)
class _WorkdirData:
    workdir: str = r"C:\Users\Admin\Downloads\mio_v23_refactored_clean"


@dataclass(frozen=True)
class _LicenseData:
    licenses: tuple[str, ...] = ("AGPL",)
    selected_license: str = "AGPL"
    license_text: str = "License text with a sufficiently long line for wrapping. " * 12


class _Controller:
    frame_count = 6

    def __init__(self) -> None:
        self.step = 0

    def main_data(self) -> _MainData:
        return _MainData()

    def workdir_data(self) -> _WorkdirData:
        return _WorkdirData()

    def set_workdir(self, path: str) -> str:
        return path

    def license_data(self) -> _LicenseData:
        return _LicenseData()

    def read_license(self, _license_name: str) -> str:
        return _LicenseData().license_text

    def read_private_notice(self) -> str:
        return "Privacy notice text. " * 40

    def initial_step(self) -> int:
        return self.step

    def persist_step(self, step: int) -> int:
        self.step = self.clamp_step(step)
        return self.step

    def clamp_step(self, step: int) -> int:
        return max(0, min(step, self.frame_count - 1))


class _TestWelcome(Welcome):
    def wait_window(self, window: tk.Misc | None = None) -> None:
        return None


def _assert_widget_tree_inside_root(root: tk.Tk, widget: tk.Misc) -> None:
    root_x = root.winfo_rootx()
    root_y = root.winfo_rooty()
    root_width = root.winfo_width()
    root_height = root.winfo_height()
    for child in widget.winfo_children():
        if child.winfo_ismapped():
            x = child.winfo_rootx() - root_x
            y = child.winfo_rooty() - root_y
            assert x >= -2, (child, x)
            assert y >= -2, (child, y)
            assert x + child.winfo_width() <= root_width + 2, (
                child,
                x,
                child.winfo_width(),
                root_width,
            )
            assert y + child.winfo_height() <= root_height + 2, (
                child,
                y,
                child.winfo_height(),
                root_height,
            )
        _assert_widget_tree_inside_root(root, child)


def _is_descendant(widget: tk.Misc, parent: tk.Misc) -> bool:
    current: tk.Misc | None = widget
    while current is not None:
        if current is parent:
            return True
        current = getattr(current, 'master', None)
    return False


def _assert_focus_traversal_uses_active_page(view: Welcome) -> None:
    inactive_pages = tuple(
        frame for step, frame in view._page_frames.items() if step != view.oobe
    )
    current: tk.Misc = view.back
    visited: set[str] = set()
    for _ in range(64):
        next_path = str(current.tk.call('tk_focusNext', str(current)))
        if not next_path or next_path in visited:
            break
        visited.add(next_path)
        current = current.nametowidget(next_path)
        assert not any(_is_descendant(current, page) for page in inactive_pages), current
    else:
        raise AssertionError('Focus traversal did not complete within 64 widgets.')


def _wait_for_root_reveal(root: tk.Tk) -> None:
    deadline = monotonic() + 2.0
    while (
        bool(getattr(root, "_appearance_alpha_gated", False))
        and monotonic() < deadline
    ):
        root.update_idletasks()
        root.update()
    assert not bool(getattr(root, "_appearance_alpha_gated", False)), (
        "Main window did not complete its first-paint reveal"
    )


def main() -> int:
    ensure_runtime_session()
    load_language_from_files("English")
    root = create_main_window()
    runtime = initialize_window_runtime(root)
    runtime.language.set("English")
    language = runtime.language
    actions = WelcomeActions(
        choose_workdir=lambda: "",
        open_workdir=lambda _path: None,
        apply_language=lambda _name: None,
        set_oobe_active=lambda _active: None,
    )
    view = _TestWelcome(
        main_window=root,
        controller=_Controller(),
        language_var=language,
        actions=actions,
        texts=lang,
    )
    reveal_window_after_layout(
        root,
        target_alpha=current_window_alpha(),
        focus=True,
    )
    stable_geometry = root.geometry()

    for step in range(6):
        view.change_page(step)
        root.update_idletasks()
        root.update()
        assert root.winfo_width() <= root.winfo_screenwidth()
        assert root.winfo_height() <= root.winfo_screenheight()
        assert view.back.winfo_ismapped()
        assert view.next.winfo_ismapped()
        assert root.geometry() == stable_geometry
        _assert_focus_traversal_uses_active_page(view)
        _assert_widget_tree_inside_root(root, view)

    view.destroy_welcome()
    compose_main_window(root)
    # Production keeps the root withdrawn while replacing the compact wizard
    # with the substantially larger main UI.  Exercise the same first-paint
    # reveal path before asserting the geometry applied by the window manager.
    reveal_window_after_layout(
        root,
        target_alpha=current_window_alpha(),
        focus=True,
    )
    _wait_for_root_reveal(root)
    assert root.winfo_width() > 1000
    assert root.sub_win2.winfo_width() > 100
    assert root.sub_win3.winfo_width() > 100
    assert root.tsk.winfo_ismapped()
    assert root.show.winfo_ismapped()
    root.destroy()
    print("WELCOME_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
