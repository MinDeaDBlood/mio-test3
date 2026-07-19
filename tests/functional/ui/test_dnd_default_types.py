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


from types import SimpleNamespace

from src.ui.common.dnd import TkinterDnD


def test_drag_and_drop_registration_uses_dnd_all_when_no_type_is_given(monkeypatch) -> None:
    calls: list[tuple[object, ...]] = []
    widget = SimpleNamespace(
        _w='.widget',
        tk=SimpleNamespace(call=lambda *args: calls.append(args)),
    )
    monkeypatch.setattr(TkinterDnD, 'TKDND_AVAILABLE', True)

    TkinterDnD.DnDWrapper.drag_source_register(widget)
    TkinterDnD.DnDWrapper.drop_target_register(widget)

    assert calls == [
        ('tkdnd::drag_source', 'register', '.widget', '*', 1),
        ('tkdnd::drop_target', 'register', '.widget', '*'),
    ]

def test_dnd_package_exports_tk_root_class() -> None:
    from src.ui.common import dnd

    assert dnd.Tk is TkinterDnD.Tk
    assert dnd.Tk.__name__ == "Tk"
    assert dnd.Tk.__module__ == "src.ui.common.dnd.TkinterDnD"

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
