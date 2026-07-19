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


import ast
from pathlib import Path

from tests.support.paths import PROJECT_ROOT
SRC_ROOT = PROJECT_ROOT / "src"


def _src_imports(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(
                alias.name for alias in node.names if alias.name.startswith("src.")
            )
        elif (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith("src.")
        ):
            imports.append(node.module)
    return tuple(imports)


def test_ui_has_no_static_dependency_on_other_project_layers() -> None:
    violations: list[str] = []
    for path in sorted((SRC_ROOT / "ui").rglob("*.py")):
        for imported in _src_imports(path):
            if imported != "src.ui" and not imported.startswith("src.ui."):
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)} imports {imported}"
                )
    assert violations == []


def test_application_resource_files_live_outside_bin() -> None:
    required = (
        PROJECT_ROOT / "config" / "settings.ini",
        PROJECT_ROOT / "config" / "context_rules.json",
        PROJECT_ROOT / "config" / "mtk_port_profiles.json",
        PROJECT_ROOT / "templates" / "ota" / "postinstall_config.txt",
        PROJECT_ROOT / "plugins" / "plugin_db.json",
        PROJECT_ROOT / "languages" / "English.json",
        PROJECT_ROOT / "languages" / "Russian.json",
    )
    assert all(path.is_file() for path in required)

    removed = (
        PROJECT_ROOT / "bin" / "setting.ini",
        PROJECT_ROOT / "bin" / "configs.json",
        PROJECT_ROOT / "bin" / "context_rules.json",
        PROJECT_ROOT / "bin" / "plugin_db.json",
        PROJECT_ROOT / "bin" / "languages",
        PROJECT_ROOT / "bin" / "config",
    )
    assert all(not path.exists() for path in removed)


def test_application_controllers_delegate_resource_io() -> None:
    checked = (
        SRC_ROOT / "app" / "settings" / "tab_controller.py",
        SRC_ROOT / "platform" / "mtk_port_profile_repository.py",
        SRC_ROOT / "app" / "welcome" / "controller.py",
    )
    forbidden_imports = {"json", "os", "shutil", "subprocess"}
    forbidden_calls = {"open", "read_text", "write_text", "read_bytes", "write_bytes"}
    violations: list[str] = []

    for path in checked:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in forbidden_imports:
                        violations.append(
                            f"{path.name}:{node.lineno} imports {alias.name}"
                        )
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.split(".")[0] in forbidden_imports:
                    violations.append(
                        f"{path.name}:{node.lineno} imports {node.module}"
                    )
            elif isinstance(node, ast.Call):
                name = ""
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    name = node.func.attr
                if name in forbidden_calls:
                    violations.append(f"{path.name}:{node.lineno} calls {name}")

    assert violations == []


def test_plugin_store_operation_state_is_not_owned_by_ui() -> None:
    ui_state = (SRC_ROOT / "ui" / "tabs" / "plugins" / "store" / "state.py").read_text(
        encoding="utf-8"
    )
    app_state = (SRC_ROOT / "app" / "plugins" / "store" / "session.py").read_text(
        encoding="utf-8"
    )
    assert "start_task" not in ui_state
    assert "start_fetch" not in ui_state
    assert "PluginStoreOperationState" in app_state
    assert "start_task" in app_state
    assert "start_fetch" in app_state


def _is_legacy_localization_key(value: str) -> bool:
    return (value.startswith("text") and value[4:].isdigit()) or (
        value.startswith("t") and value[1:].isdigit()
    )


def test_ui_and_application_use_semantic_localization_keys() -> None:
    violations: list[str] = []
    for layer in ("ui", "app"):
        for path in sorted((SRC_ROOT / layer).rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                key: str | None = None
                if isinstance(node, ast.Attribute):
                    key = node.attr
                elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                    key = node.value
                if key is not None and _is_legacy_localization_key(key):
                    violations.append(
                        f"{path.relative_to(PROJECT_ROOT)}:{node.lineno} uses {key}"
                    )
    assert violations == []


def test_logic_runtime_contexts_do_not_accept_opaque_application_state() -> None:
    checked = (
        SRC_ROOT / "logic" / "projects" / "unpack" / "runtime_context.py",
        SRC_ROOT / "logic" / "projects" / "pack" / "runtime_context.py",
        SRC_ROOT / "logic" / "projects" / "convert" / "runtime_context.py",
    )
    forbidden_fields = {
        "settings",
        "current_project_name",
        "module_manager",
    }
    violations: list[str] = []
    for path in checked:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.AnnAssign) or not isinstance(
                node.target, ast.Name
            ):
                continue
            if node.target.id in forbidden_fields:
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{node.lineno} owns {node.target.id}"
                )
            if isinstance(node.annotation, ast.Name) and node.annotation.id == "object":
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{node.lineno} uses opaque object for {node.target.id}"
                )
    assert violations == []

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
