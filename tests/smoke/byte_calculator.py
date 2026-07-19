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


import sys

sys.path.insert(0, '.')

from tests.support.runtime_smoke import prepare_root
from src.app.composition.byte_calculator import open_byte_calculator_window


def select_unit(window, combobox, unit: str) -> None:
    values = tuple(combobox.cget('values'))
    combobox.current(values.index(unit))
    combobox.event_generate('<<ComboboxSelected>>')
    window.update()


root = prepare_root()
window = open_byte_calculator_window()
window.withdraw()
window.update_idletasks()

# Input on the left: 2 MB must become 2048 KB on the right.
window.origin_unit.set('MB')
window.target_unit.set('KB')
window.origin_size_var.set('2')
window.calc_forward()
assert window.origin_size_var.get() == '2'
assert window.result_size_var.get() == '2048'

# Changing the right selector must refresh only the right field.
select_unit(window, window.target_unit, 'B')
assert window.origin_size_var.get() == '2'
assert window.result_size_var.get() == '2097152'

# Changing the left selector must refresh only the left field.
select_unit(window, window.origin_unit, 'KB')
assert window.origin_size_var.get() == '2048'
assert window.result_size_var.get() == '2097152'

# Input on the right: 1024 B must become 1 KB on the left.
window.origin_unit.set('KB')
window.target_unit.set('B')
window.result_size_var.set('1024')
window.calc_reverse()
assert window.result_size_var.get() == '1024'
assert window.origin_size_var.get() == '1'

window.destroy()
root.destroy()
print('BYTE_CALCULATOR_SMOKE_OK')

if __name__ == "__main__":
    from tests.support.direct_execution import support_module_main

    raise SystemExit(support_module_main(__file__))
