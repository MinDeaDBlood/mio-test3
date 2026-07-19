
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

from src.app.composition.main_window import compose_main_window, create_main_window
from src.app.runtime.session import ensure_runtime_session
from src.app.composition.window_runtime import initialize_window_runtime
from src.app.localization import load_language_from_files
from src.app.localization_runtime import lang
from src.app.std_streams import get_stdout_router
from src.ui.common.window_appearance import apply_transparency_to_windows
from src.ui.common.window_reveal import reveal_window_after_layout
from src.ui.common.windowing import Toplevel
from src.ui import startup_status_keys as startup_keys
from src.ui.startup_status import present_basic_mode_notice, present_startup_duration

ensure_runtime_session()
load_language_from_files("English")
root = create_main_window()
root.withdraw()
initialize_window_runtime(root)
compose_main_window(root)
reveal_window_after_layout(root, target_alpha=1.0, focus=False)
root.update()
assert root.winfo_ismapped()
assert root.winfo_width() >= 960
assert root.winfo_height() >= 600
assert root.sub_win2.winfo_width() > 100
assert root.sub_win3.winfo_width() > 100
assert root.tsk.winfo_exists()
assert root.show.winfo_exists()

stdout_router = get_stdout_router()
present_basic_mode_notice(
    texts=lang, emit=lambda message: stdout_router.write(message + "\n")
)
present_startup_duration(
    1.25, texts=lang, emit=lambda message: stdout_router.write(message + "\n")
)
root.update()
log_text = root.show.get("1.0", "end")
assert (
    lang.resolve_required_ui_text(
        startup_keys.STARTUP_STATUS_HOME_WELCOME_MESSAGE
    ).splitlines()[0]
    in log_text
)
assert (
    lang.resolve_required_ui_text(startup_keys.STARTUP_STATUS_STARTUP_DURATION_FORMAT)
    % 1.25
).splitlines()[0] in log_text

apply_transparency_to_windows(enabled=True, effect_alpha=0.84)
root.update_idletasks()
assert abs(float(root.attributes("-alpha")) - 0.84) < 0.01
child = Toplevel(master=root)
child.update_idletasks()
assert abs(float(child.attributes("-alpha")) - 0.84) < 0.01
apply_transparency_to_windows(enabled=False)
root.update_idletasks()
child.update_idletasks()
assert abs(float(root.attributes("-alpha")) - 1.0) < 0.01
assert abs(float(child.attributes("-alpha")) - 1.0) < 0.01
child.destroy()
root.destroy()
print("UI_SMOKE_OK")

if __name__ == "__main__":
    from tests.support.direct_execution import support_module_main

    raise SystemExit(support_module_main(__file__))
