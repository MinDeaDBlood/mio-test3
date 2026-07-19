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


from pathlib import Path

from src.core.paths import resolve_program_root


def test_source_root_is_derived_from_module_location_not_argv(tmp_path: Path) -> None:
    module_file = tmp_path / 'mio' / 'src' / 'core' / 'paths.py'
    assert resolve_program_root(
        frozen=False,
        module_file=str(module_file),
    ) == tmp_path / 'mio'


def test_frozen_root_is_executable_directory(tmp_path: Path) -> None:
    executable = tmp_path / 'mio' / 'MIO-KITCHEN'
    assert resolve_program_root(
        frozen=True,
        executable=str(executable),
        platform_name='Linux',
    ) == tmp_path / 'mio'


def test_macos_bundle_root_is_outside_app_bundle(tmp_path: Path) -> None:
    executable = tmp_path / 'MIO' / 'tool.app' / 'Contents' / 'MacOS' / 'tool'
    assert resolve_program_root(
        frozen=True,
        executable=str(executable),
        platform_name='Darwin',
    ) == tmp_path / 'MIO'

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
