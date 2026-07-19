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

from tests.support.paths import PROJECT_ROOT


def test_src_contains_no_script_modules_or_script_directories() -> None:
    src_root = PROJECT_ROOT / "src"
    offenders = [
        path.relative_to(PROJECT_ROOT).as_posix()
        for path in src_root.rglob("*")
        if (
            path.is_dir()
            and path.name.lower() == "scripts"
            or path.is_file()
            and path.suffix == ".py"
            and path.stem.lower().startswith("script")
        )
    ]

    assert offenders == []


def test_manual_quality_configuration_lives_under_scripts() -> None:
    assert (PROJECT_ROOT / "scripts/config/pytest.ini").is_file()
    assert (PROJECT_ROOT / "scripts/config/mypy-typed-boundaries.ini").is_file()
    assert not (PROJECT_ROOT / "pytest.ini").exists()
    assert not (PROJECT_ROOT / "mypy-typed-boundaries.ini").exists()


def test_unused_root_environment_files_stay_removed() -> None:
    assert not (PROJECT_ROOT / "assets").exists()
    assert not (PROJECT_ROOT / "constraints-release.txt").exists()
    assert not (PROJECT_ROOT / "shell.nix").exists()


def test_github_build_does_not_run_repository_check_scripts() -> None:
    workflow = (PROJECT_ROOT / ".github/workflows/build.yml").read_text(
        encoding="utf-8"
    )

    for forbidden in (
        "scripts/manual/",
        "scripts/quality/",
        "scripts/audits/",
        "scripts/arch_guard/",
        "pytest",
        "mypy",
        "ruff",
    ):
        assert forbidden not in workflow


if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
