#!/usr/bin/env python3
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


import argparse
from pathlib import Path
from threading import Thread
from time import monotonic, sleep



from src.app.entrypoint import ensure_runtime_session
from src.app.runtime.window_access import require_main_window
from src.app.runtime.core_access import require_settings
from src.app.runtime.defaults_access import require_states

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _quit_mainloop_after_real_startup(*, timeout: float = 30.0) -> None:
    deadline = monotonic() + timeout
    states = require_states()
    while not states.inited:
        if monotonic() >= deadline:
            raise TimeoutError("Application startup did not reach the initialized state")
        sleep(0.01)
    root = require_main_window()
    root.after(0, root.quit)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Collect runtime metric observations through the smoke flow.')
    arguments = (
        _direct_sys.argv[1:]
        if argv is None and __name__ == "__main__"
        else (argv or [])
    )
    parser.parse_args(arguments)
    ensure_runtime_session()
    settings = require_settings()
    states = require_states()
    setattr(settings, 'check_upgrade', '0')
    setattr(settings, 'updating', 'false')
    setattr(settings, 'oobe', '5')
    setattr(states, 'in_oobe', False)

    import src.app.bootstrap as bootstrap
    from src.app.composition.plugin_store import open_plugin_store

    stopper = Thread(target=_quit_mainloop_after_real_startup, daemon=True)
    stopper.start()
    root = None
    try:
        composition = bootstrap._init_tk([])
        stopper.join(timeout=5)
        if composition is None:
            raise RuntimeError("Main window composition was not created")
        root = require_main_window()
        root.update_idletasks()
        composition.project_workspace_host.ensure_workspace()
        root.update_idletasks()
        composition.plugin_manager_host.ensure_manager()
        root.update_idletasks()
        store = open_plugin_store()
        try:
            if getattr(store, 'winfo_exists', lambda: False)():
                store.update_idletasks()
        finally:
            try:
                if getattr(store, 'winfo_exists', lambda: False)():
                    store.destroy()
            except Exception:
                pass
    finally:
        if root is not None and root.winfo_exists():
            root.destroy()
    print('METRIC_COLLECTION_OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
