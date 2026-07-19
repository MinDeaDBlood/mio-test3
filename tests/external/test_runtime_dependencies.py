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


import json


from scripts.quality import check_required_dependencies as deps


def test_dependency_inventory_covers_release_smoke_boundaries() -> None:
    imports = {spec.import_name for spec in deps.DEPENDENCIES}
    assert {"google.protobuf", "Crypto", "zstandard", "sv_ttk", "tkinter"} <= imports

    required = {spec.import_name for spec in deps.DEPENDENCIES if spec.required}
    assert {"google.protobuf", "Crypto", "zstandard", "tkinter"} <= required


def test_dependency_checker_reports_environment_without_importing_app(
    monkeypatch,
) -> None:
    # Unit-test the report shape without importing real GUI/native dependencies
    # into the pytest process. The real dependency import path is covered by the
    # CLI smoke test, where it runs in an isolated subprocess like release CI.
    fake_statuses = [
        deps.DependencyStatus(
            "google.protobuf", "protobuf", "runtime", True, True, "6.0", None
        ),
        deps.DependencyStatus("tkinter", None, "ui", True, True, None, None),
    ]
    monkeypatch.setattr(deps, "collect_statuses", lambda **_kwargs: fake_statuses)
    monkeypatch.setattr(deps, "validate_protobuf_namespace", lambda _statuses: [])

    report = deps.build_report(include_optional=False, categories=["runtime", "ui"])
    by_import = {item["import_name"]: item for item in report["dependencies"]}
    by_spec = {spec.import_name: spec for spec in deps.DEPENDENCIES}

    assert report["python"]
    assert by_import["google.protobuf"]["category"] == "runtime"
    assert by_import["tkinter"]["category"] == "ui"
    assert by_spec["sv_ttk"].required is False
    assert by_import["google.protobuf"]["ok"] is True


def test_dependency_checker_cli_can_run_as_diagnostic_json(monkeypatch, capsys) -> None:
    fake_statuses = [
        deps.DependencyStatus(
            "google.protobuf", "protobuf", "runtime", True, True, "6.0", None
        ),
        deps.DependencyStatus("tkinter", None, "ui", True, True, None, None),
    ]
    monkeypatch.setattr(deps, "collect_statuses", lambda **_kwargs: fake_statuses)
    monkeypatch.setattr(deps, "validate_protobuf_namespace", lambda _statuses: [])

    assert deps.main(["--json", "--allow-missing-required"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert any(
        item["import_name"] == "google.protobuf" for item in report["dependencies"]
    )

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
