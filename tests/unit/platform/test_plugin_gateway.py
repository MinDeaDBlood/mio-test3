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
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.logic.plugins.execution_plan import plan_plugin_execution
from src.platform.plugin_gateway import PluginGateway
import src.platform.plugins.execution as execution


class _Loader:
    def __init__(self) -> None:
        self.virtual: dict[str, object] = {}
        self.functions: dict[tuple[str, object], object] = {}

    def register(self, plugin_id: str, entry: object, func: object) -> None:
        self.functions[(plugin_id, entry)] = func

    def is_registered(self, plugin_id: str) -> bool:
        return any(key[0] == plugin_id for key in self.functions)

    def run(self, plugin_id: str, entry: object, *, mapped_args):
        return self.functions[(plugin_id, entry)](**mapped_args)

    def run_entry(self, entry: object) -> None:
        for (plugin_id, current_entry), func in tuple(self.functions.items()):
            if current_entry == entry:
                func()


class _Manager:
    def __init__(self, module_dir: Path) -> None:
        self.module_dir = str(module_dir)
        self.addon_loader = _Loader()
        self.addon_entries = SimpleNamespace(
            main="main",
            before_pack="before_pack",
            packing="packing",
            close="close",
        )
        self.notified = 0
        self.refreshes = 0
        self.load_claimed = False

    def claim_background_load(self) -> bool:
        if self.load_claimed:
            return False
        self.load_claimed = True
        return True

    def list_packages(self) -> list[str]:
        return sorted(path.name for path in Path(self.module_dir).iterdir() if path.is_dir())

    def notify_plugin_state_changed(self, plugin_id: str | None = None) -> None:
        self.notified += 1

    def request_plugin_list_refresh(self) -> bool:
        self.refreshes += 1
        return True

    def is_installed(self, plugin_id: str) -> bool:
        return (Path(self.module_dir) / plugin_id).is_dir()

    def is_virtual(self, plugin_id: str) -> bool:
        return plugin_id in self.addon_loader.virtual

    def get_name(self, plugin_id: str) -> str:
        return plugin_id

    def install(self, package_path: str):
        return "normal", package_path

    def uninstall_plugin(self, plugin_id: str, *, include_dependents: bool = True):
        return True, "", [plugin_id]

    def export(self, plugin_id: str, *, output_dir: str, output=None):
        return 0

    def check_mpk(self, path: str):
        return "normal", path

    def create_plugin_scaffold(self, data: dict):
        return data["id"]

    def plugin_config_path(self, plugin_id: str) -> str | None:
        return None

    def collect_dependent_plugin_ids(self, plugin_id: str) -> list[str]:
        return []


def _execute_plan(
    gateway: PluginGateway,
    plugin_id: str,
    *,
    tmp_path: Path,
    values: dict[str, object],
) -> int:
    inspection = gateway.inspect_execution(plugin_id)
    plan = plan_plugin_execution(
        plugin_id,
        project_name="demo",
        inspection=inspection,
    )
    assert plan.can_execute
    assert plan.entry_kind is not None
    return gateway.execute_planned(
        plugin_id,
        entry_kind=plan.entry_kind.value,
        entry_path=plan.entry_path,
        project_work_path=str(tmp_path / "work"),
        project_output_path=str(tmp_path / "output"),
        tool_bin=str(tmp_path / "bin"),
        tool_version="1.0",
        language="English",
        temp_path=str(tmp_path / "temp"),
        module_exec=str(tmp_path / "module_exec.sh"),
        values=values,
    )


def test_python_plugin_is_inspected_planned_and_executed(tmp_path: Path) -> None:
    module_dir = tmp_path / "plugins"
    plugin_dir = module_dir / "demo.plugin"
    plugin_dir.mkdir(parents=True)
    marker = tmp_path / "plugin-ran.txt"
    (plugin_dir / "info.json").write_text(json.dumps({"depend": ""}), encoding="utf-8")
    (plugin_dir / "main.py").write_text(
        "def main(marker_path, value):\n"
        "    from pathlib import Path\n"
        "    Path(marker_path).write_text(value, encoding='utf-8')\n",
        encoding="utf-8",
    )
    gateway = PluginGateway(_Manager(module_dir))

    gateway.load_plugins_and_notify()
    result = _execute_plan(
        gateway,
        "demo.plugin",
        tmp_path=tmp_path,
        values={"marker_path": str(marker), "value": "completed"},
    )

    assert result == 0
    assert marker.read_text(encoding="utf-8") == "completed"


def test_shell_plugin_command_is_logged_without_export_values(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module_dir = tmp_path / "plugins"
    plugin_dir = module_dir / "shell.plugin"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "info.json").write_text(json.dumps({"depend": ""}), encoding="utf-8")
    (plugin_dir / "main.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    captured: dict[str, object] = {}

    def fake_call(command, extra_path=True, out=True, *, log_command=None):
        captured["command"] = command
        captured["log_command"] = log_command
        return 0

    monkeypatch.setattr(execution, "call", fake_call)
    gateway = PluginGateway(_Manager(module_dir))

    result = _execute_plan(
        gateway,
        "shell.plugin",
        tmp_path=tmp_path,
        values={"ACCESS_TOKEN": "top-secret"},
    )

    assert result == 0
    assert "top-secret" in str(captured["command"])
    assert "top-secret" not in str(captured["log_command"])
    assert "redacted" in str(captured["log_command"])


if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
