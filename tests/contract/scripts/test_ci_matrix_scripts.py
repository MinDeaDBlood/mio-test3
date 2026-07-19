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


import subprocess
import sys
from tests.support.paths import PROJECT_ROOT


def _dry_run(script: str, *args: str) -> str:
    result = subprocess.run(
        [sys.executable, script, "--dry-run", *args],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=True,
    )
    return result.stdout


def test_ci_unit_contracts_runs_arch_guard_and_complete_pytest_suite() -> None:
    output = _dry_run("scripts/manual/manual_unit_contracts.py")
    assert "architecture_guard:" in output
    assert "scripts/arch_guard/main.py" in output
    assert output.count("-m pytest -q --rootdir=. -c scripts/config/pytest.ini") == 1
    assert "scripts/config/pytest.ini tests" in output
    assert "-k not smoke" not in output


def test_ci_release_preflight_has_install_and_strict_release_checks() -> None:
    output = _dry_run("scripts/manual/manual_release_preflight.py")
    assert "scripts/quality/check_system_dependencies.py" in output
    assert "pip install -r requirements.txt" in output
    assert "scripts/quality/check_required_dependencies.py --smoke-only" in output
    assert (
        "scripts/quality/check_localization_keys.py --max-warning-issues 15 --max-missing-keys-per-language 165"
        in output
    )


def test_ci_release_preflight_can_skip_install_for_prepared_environment() -> None:
    output = _dry_run("scripts/manual/manual_release_preflight.py", "--skip-install")
    assert "pip install" not in output
    assert "scripts/quality/check_required_dependencies.py --smoke-only" in output


def test_ci_gui_smoke_uses_xvfb_wrapped_gui_scripts() -> None:
    output = _dry_run("scripts/manual/manual_gui_smoke.py")
    assert "tests/smoke/targeted.py" in output
    assert "tests/smoke/runtime.py" in output
    assert "tests/e2e/main_flow.py" in output
    assert "ui_smoke:" in output


def test_ci_gui_smoke_full_delegates_to_runtime_suite() -> None:
    output = _dry_run("scripts/manual/manual_gui_smoke.py", "--full")
    assert "scripts/manual/runtime_smoke_suite.py" in output
    assert "tests/e2e/main_flow.py" not in output


def test_ci_release_archive_builds_release_zip_contour() -> None:
    output = _dry_run("scripts/release/release_archive.py", "--skip-checks")
    assert "scripts/release/build_release_archive.py --skip-checks --output" in output


def test_ci_release_preflight_skip_install_prepared_environment() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/manual/manual_release_preflight.py", "--help"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=True,
    )
    assert "Prepared-environment mode" in result.stdout
    assert "Python runtime dependencies must" in result.stdout
    assert "already be installed" in result.stdout


def test_system_dependency_checker_is_known_prerequisite_preflight() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/quality/check_system_dependencies.py", "--help"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=True,
    )
    assert "known OS-level release/build prerequisites" in result.stdout
    assert "not a complete system verifier" in result.stdout


def _make_guard_context(tmp_path):
    from scripts.arch_guard.reporting import GuardContext

    (tmp_path / "scripts").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "scripts" / "ci_common.py").write_text("", encoding="utf-8")
    return GuardContext(project_root=tmp_path, src_dir=tmp_path / "src")


def _run_exit_guard(tmp_path, rel_path: str, source: str) -> list[str]:
    from scripts.arch_guard.layer_rules import check_ci_wrapper_exit_boundary

    ctx = _make_guard_context(tmp_path)
    target = tmp_path / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    check_ci_wrapper_exit_boundary(ctx)
    return ctx.violations


def test_ci_exit_guard_rejects_aliased_os_exit(tmp_path) -> None:
    violations = _run_exit_guard(
        tmp_path,
        "src/bad_exit.py",
        "import os as operating_system\noperating_system._exit(1)\n",
    )
    assert any("os._exit" in violation for violation in violations)


def test_ci_exit_guard_rejects_from_os_import_exit(tmp_path) -> None:
    violations = _run_exit_guard(
        tmp_path,
        "src/bad_exit.py",
        "from os import _exit\n_exit(1)\n",
    )
    assert any("from os import _exit" in violation for violation in violations)
    assert any("os._exit alias" in violation for violation in violations)


def test_ci_exit_guard_rejects_simple_exit_alias_assignment(tmp_path) -> None:
    violations = _run_exit_guard(
        tmp_path,
        "src/bad_exit.py",
        "import os as operating_system\nhard_exit = operating_system._exit\nhard_exit(1)\n",
    )
    assert any("aliasing os._exit" in violation for violation in violations)
    assert any("os._exit alias" in violation for violation in violations)


def test_ci_exit_guard_rejects_literal_importlib_os_exit(tmp_path) -> None:
    violations = _run_exit_guard(
        tmp_path,
        "src/bad_exit.py",
        'import importlib as il\nil.import_module("os")._exit(1)\n',
    )
    assert any(
        'importlib.import_module("os")._exit' in violation for violation in violations
    )


def test_ci_exit_guard_rejects_plain_os_exit_alias_assignment(tmp_path) -> None:
    violations = _run_exit_guard(
        tmp_path,
        "src/bad_exit.py",
        "import os\nhard_exit = os._exit\nhard_exit(1)\n",
    )
    assert any("aliasing os._exit" in violation for violation in violations)
    assert any("os._exit alias" in violation for violation in violations)


def test_ci_exit_guard_rejects_from_importlib_import_module_os_exit(tmp_path) -> None:
    violations = _run_exit_guard(
        tmp_path,
        "src/bad_exit.py",
        'from importlib import import_module\nimport_module("os")._exit(1)\n',
    )
    assert any(
        'importlib.import_module("os")._exit' in violation for violation in violations
    )


def test_ci_exit_guard_allows_normal_system_exit(tmp_path) -> None:
    violations = _run_exit_guard(
        tmp_path,
        "scripts/manual/manual_unit_contracts.py",
        "def main():\n"
        "    return 0\n\n"
        'if __name__ == "__main__":\n'
        "    raise SystemExit(main())\n",
    )
    assert violations == []
