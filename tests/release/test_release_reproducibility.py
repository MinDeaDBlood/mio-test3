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


import zipfile
import json
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from types import SimpleNamespace
from pathlib import Path

from tests.support.paths import PROJECT_ROOT


def _project_script(relative_path: str) -> str:
    return str(PROJECT_ROOT / relative_path)


def _run_script_main(module_name: str, *args: str) -> SimpleNamespace:
    module = __import__(module_name, fromlist=["main"])
    stdout = StringIO()
    stderr = StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        returncode = module.main(list(args))
    return SimpleNamespace(
        returncode=returncode,
        stdout=stdout.getvalue(),
        stderr=stderr.getvalue(),
    )


def _run_localization_checker(*args: str) -> SimpleNamespace:
    from scripts.quality.check_localization_keys import main

    stdout = StringIO()
    stderr = StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        returncode = main(list(args))
    return SimpleNamespace(
        returncode=returncode,
        stdout=stdout.getvalue(),
        stderr=stderr.getvalue(),
    )


def _run_release_archive(*args: str) -> SimpleNamespace:
    from scripts.release.build_release_archive import main

    stdout = StringIO()
    stderr = StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        returncode = main(list(args))
    return SimpleNamespace(
        returncode=returncode,
        stdout=stdout.getvalue(),
        stderr=stderr.getvalue(),
    )


def _make_release_root(root: Path) -> Path:
    for directory in (
        "bin",
        "config",
        "docs",
        "languages",
        "plugins/installed",
        "readmes",
        "scripts/bin/temp",
        "src",
        "temp/plugins/downloads",
        "temp/plugins/runtime",
        "temp/updates",
        "temp/magisk",
        "temp/mtk_port",
        "templates",
        "tests",
        "logs",
        "Projects",
    ):
        (root / directory).mkdir(parents=True, exist_ok=True)

    (root / "tool").write_text("runtime executable", encoding="utf-8")
    (root / "bin/runtime.bin").write_bytes(b"runtime")
    (root / "config/settings.ini").write_text("[setting]\n", encoding="utf-8")
    (root / "plugins/plugin_db.json").write_text("{}\n", encoding="utf-8")
    (root / "templates/example.txt").write_text("template\n", encoding="utf-8")
    for directory in ("docs", "readmes", "scripts", "src", "tests"):
        (root / directory / "repository-only.txt").write_text(
            "repository only\n", encoding="utf-8"
        )
    (root / "README.md").write_text("fixture project\n", encoding="utf-8")
    (root / "build.py").write_text("repository build script\n", encoding="utf-8")
    (root / "requirements.txt").write_text("", encoding="utf-8")
    (root / "languages/English.json").write_text("{}\n", encoding="utf-8")
    (root / "languages/Russian.json").write_text("{}\n", encoding="utf-8")
    return root


def test_dependency_checker_smoke_only_matches_runtime_ui_required_set() -> None:
    proc = _run_script_main(
        "scripts.quality.check_required_dependencies",
        "--smoke-only",
        "--json",
        "--allow-missing-required",
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "google.protobuf" in proc.stdout
    assert "PyInstaller" not in proc.stdout
    assert "chlorophyll" not in proc.stdout


def test_release_archive_excludes_generated_runtime_contents(tmp_path: Path) -> None:
    release_root = _make_release_root(tmp_path / "project")
    temp_log = (
        release_root / "temp" / "plugins" / "downloads" / "release-repro-test.log"
    )
    log_file = release_root / "logs" / "release-repro-test.log"
    stray_script_log = release_root / "scripts" / "bin" / "temp" / "historical.log"
    generated_project = release_root / "Projects" / "Smoke" / "input" / "system.img"
    temp_log.write_text("generated runtime temp log", encoding="utf-8")
    log_file.write_text("generated runtime app log", encoding="utf-8")
    stray_script_log.write_text("historical runtime log", encoding="utf-8")
    generated_project.parent.mkdir(parents=True)
    generated_project.write_bytes(b"generated project image")
    output = tmp_path / "release.zip"

    result = _run_release_archive(
        "--skip-checks",
        "--root",
        str(release_root),
        "--output",
        str(output),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
        unique_names = set(names)

    assert "temp/plugins/downloads/release-repro-test.log" not in unique_names
    assert "logs/release-repro-test.log" not in unique_names
    assert "scripts/bin/temp/historical.log" not in unique_names
    assert "Projects/Smoke/input/system.img" not in unique_names
    assert not any(name.startswith("Projects/") for name in unique_names)
    for repository_only in ("docs/", "readmes/", "scripts/", "src/", "tests/"):
        assert not any(name.startswith(repository_only) for name in unique_names)
    assert "README.md" not in unique_names
    assert "build.py" not in unique_names
    assert "requirements.txt" not in unique_names
    assert "tool" in unique_names
    assert "bin/runtime.bin" in unique_names
    assert "config/settings.ini" in unique_names
    assert "plugins/plugin_db.json" in unique_names
    assert "temp/plugins/downloads/" in unique_names
    assert "temp/plugins/runtime/" in unique_names
    assert "temp/updates/" in unique_names
    assert "temp/magisk/" in unique_names
    assert "temp/mtk_port/" in unique_names
    assert "plugins/installed/" in unique_names
    assert "bin/temp/" not in unique_names
    assert "bin/module/" not in unique_names
    assert "logs/" in unique_names
    assert len(names) == len(unique_names)


def test_localization_checker_reports_release_smoke_contract() -> None:
    proc = _run_localization_checker("--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "English" in proc.stdout
    assert "Russian" in proc.stdout
    assert "required_keys" in proc.stdout
    assert "missing_reference_keys" in proc.stdout


def test_localization_checker_strict_mode_blocks_incomplete_translation(
    tmp_path: Path,
) -> None:
    language_dir = tmp_path / "languages"
    language_dir.mkdir(parents=True)
    (language_dir / "English.json").write_text(
        '{"toolbox": "Tools", "warn1": "Pick a project"}', encoding="utf-8"
    )
    (language_dir / "Russian.json").write_text(
        '{"toolbox": "Инструменты", "warn1": "Выберите проект"}', encoding="utf-8"
    )
    (language_dir / "Deutsch.json").write_text(
        '{"toolbox": "Werkzeuge", "warn1": "None"}', encoding="utf-8"
    )

    non_strict = _run_localization_checker(
        "--root",
        str(tmp_path),
        "--required-key",
        "toolbox",
        "--required-key",
        "warn1",
    )
    assert non_strict.returncode == 0, non_strict.stdout + non_strict.stderr

    strict = _run_localization_checker(
        "--root",
        str(tmp_path),
        "--required-key",
        "toolbox",
        "--required-key",
        "warn1",
        "--strict",
    )
    assert strict.returncode == 1
    assert "Invalid translation values" in strict.stdout


def test_release_archive_includes_manifest_with_file_hashes(tmp_path: Path) -> None:
    from scripts.release.build_release_archive import build_archive

    release_root = _make_release_root(tmp_path / "project")
    (release_root / "release_manifest.json").write_text(
        '{"stale": true}\n', encoding="utf-8"
    )
    output = tmp_path / "release-with-manifest.zip"
    build_archive(output, run_checks=False, project_root=release_root)
    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())
        manifest = archive.read("release_manifest.json").decode("utf-8")

    assert "release_manifest.json" in names
    assert '"schema_version": 1' in manifest
    assert '"stale"' not in manifest
    assert '"dependency_inventory"' in manifest
    assert '"localization_report"' in manifest
    assert '"archive"' in manifest
    assert '"sha256"' in manifest
    assert "languages/English.json" in manifest
    assert "scripts/repository-only.txt" not in manifest
    assert "python scripts/quality/check_typed_boundaries.py" in manifest


def test_release_archive_can_omit_manifest_for_legacy_packaging(tmp_path: Path) -> None:
    release_root = _make_release_root(tmp_path / "project")
    output = tmp_path / "release-no-manifest.zip"
    result = _run_release_archive(
        "--skip-checks",
        "--no-manifest",
        "--root",
        str(release_root),
        "--output",
        str(output),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())

    assert "release_manifest.json" not in names



def test_localization_json_mode_is_machine_readable_only() -> None:
    result = _run_localization_checker("--json")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["blocking_issue_count"] == 0
    assert "LOCALIZATION_KEYS_OK" not in result.stdout


def test_localization_checker_warning_budget_is_enforced() -> None:
    ok = _run_localization_checker(
        "--json",
        "--max-warning-issues",
        "15",
        "--max-missing-keys-per-language",
        "165",
    )
    assert ok.returncode == 0, ok.stdout + ok.stderr
    payload = json.loads(ok.stdout)
    assert payload["warning_budget"]["violation_count"] == 0

    failing = _run_localization_checker(
        "--json",
        "--max-warning-issues",
        "0",
    )
    assert failing.returncode == 1
    payload = json.loads(failing.stdout)
    assert payload["warning_budget"]["violation_count"] > 0


def test_localization_invalid_deutsch_hungarian_values_are_cleaned() -> None:
    result = _run_localization_checker("--json")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    invalid_by_language = {
        item["language"]: set(item["keys"]) for item in payload["invalid_values"]
    }
    assert "Deutsch" not in invalid_by_language
    assert "Hungarian" not in invalid_by_language


def test_system_dependency_checker_reports_json_shape_without_importing_runtime() -> (
    None
):
    result = _run_script_main(
        "scripts.quality.check_system_dependencies",
        "--json",
        "--allow-missing",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert "platform" in payload
    assert "issues" in payload
    assert "ok" in payload

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
