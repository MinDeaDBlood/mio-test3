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

PROJECT_ROOT = _DIRECT_PROJECT_ROOT
APP_ROOT = PROJECT_ROOT / "src" / "app"


def test_application_workflows_do_not_call_module_manager_internals() -> None:
    workflow_roots = (
        APP_ROOT / "plugins",
        APP_ROOT / "projects",
    )
    workflow_files = [APP_ROOT / "process_lifecycle.py"]
    for root in workflow_roots:
        workflow_files.extend(root.rglob("*.py"))
    forbidden_tokens = (
        "module_manager.run",
        "self.module_manager",
        ".addon_loader",
        ".addon_entries",
    )
    violations: list[str] = []
    for path in workflow_files:
        source = path.read_text(encoding="utf-8")
        if any(token in source for token in forbidden_tokens):
            violations.append(path.relative_to(PROJECT_ROOT).as_posix())
    assert violations == []


def test_plugin_execution_is_split_by_layer() -> None:
    controller = (APP_ROOT / "plugins/manager_controller.py").read_text(
        encoding="utf-8"
    )
    planner = (
        PROJECT_ROOT / "src/logic/plugins/execution_plan.py"
    ).read_text(encoding="utf-8")
    gateway = (PROJECT_ROOT / "src/platform/plugin_gateway.py").read_text(
        encoding="utf-8"
    )
    execution = (
        PROJECT_ROOT / "src/platform/plugins/execution.py"
    ).read_text(encoding="utf-8")

    assert "plan_plugin_execution" in controller
    assert "inspect_execution" in controller
    assert "execute_planned" in controller
    assert "def plan_plugin_execution" in planner
    assert "Path(" not in planner
    assert "open(" not in planner
    assert "def inspect_execution" in gateway
    assert "json.loads" in gateway
    assert "imp.load_source" in gateway
    assert "class PluginExecutionAdapter" in execution
    assert "addon_loader.run" in execution
    assert "src.logic" not in execution
    assert "src.logic" not in gateway


if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
