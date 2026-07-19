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

from src.logic.plugins.execution_plan import PluginEntryKind, plan_plugin_execution


def test_execution_requires_selected_project() -> None:
    plan = plan_plugin_execution(
        "demo.plugin",
        project_name="",
        inspection={"plugin_name": "Demo", "virtual": True},
    )
    assert not plan.can_execute
    assert plan.error_code == "project_not_selected"


def test_missing_dependency_is_rejected_by_logic() -> None:
    plan = plan_plugin_execution(
        "demo.plugin",
        project_name="demo",
        inspection={
            "plugin_name": "Demo",
            "virtual": False,
            "plugin_exists": True,
            "manifest_state": "valid",
            "missing_dependencies": ("base.plugin",),
            "python_entry_path": "/plugins/demo/main.py",
        },
    )
    assert not plan.can_execute
    assert plan.error_code == "plugin_dependency_missing"
    assert plan.error_params["dependency"] == "base.plugin"


def test_shell_entry_keeps_legacy_precedence_over_python() -> None:
    plan = plan_plugin_execution(
        "demo.plugin",
        project_name="demo",
        inspection={
            "plugin_name": "Demo",
            "virtual": False,
            "plugin_exists": True,
            "manifest_state": "valid",
            "missing_dependencies": (),
            "python_entry_path": "/plugins/demo/main.py",
            "shell_entry_path": "/plugins/demo/main.sh",
        },
    )
    assert plan.can_execute
    assert plan.entry_kind is PluginEntryKind.SHELL
    assert plan.entry_path.endswith("main.sh")


if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
