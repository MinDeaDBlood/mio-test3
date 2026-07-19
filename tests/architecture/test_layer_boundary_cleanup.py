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
import pytest


from tests.support.paths import PROJECT_ROOT
SRC_ROOT = PROJECT_ROOT / 'src'


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_removed_mtk_compatibility_package_does_not_return() -> None:
    assert not (SRC_ROOT / 'porttool').exists()
    assert (SRC_ROOT / 'core' / 'mtk_port').is_dir()
    assert (SRC_ROOT / 'logic' / 'tools' / 'mtk_port_tool' / 'operation.py').is_file()


def test_ui_depends_on_application_only_through_the_legacy_entrypoint() -> None:
    allowed = {SRC_ROOT / 'ui' / 'tool.py': {'src.app.entrypoint'}}
    for path in (SRC_ROOT / 'ui').rglob('*.py'):
        imports = _imports(path)
        app_imports = {
            name for name in imports
            if name == 'src.app' or name.startswith('src.app.')
        }
        assert app_imports == allowed.get(path, set()), path


def test_ui_localization_is_an_injected_protocol_without_global_state() -> None:
    localization_path = SRC_ROOT / 'ui' / 'localization.py'
    tree = ast.parse(localization_path.read_text(encoding='utf-8'), filename=str(localization_path))
    assigned_names = {
        target.id
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in ((node.targets if isinstance(node, ast.Assign) else [node.target]))
        if isinstance(target, ast.Name)
    }
    assert 'lang' not in assigned_names
    assert 'bind_localization' not in localization_path.read_text(encoding='utf-8')
    for path in (SRC_ROOT / 'ui').rglob('*.py'):
        source = path.read_text(encoding='utf-8')
        assert 'from src.ui.localization import lang' not in source, path


def test_config_does_not_depend_on_application_logic_or_ui() -> None:
    for path in (SRC_ROOT / 'config').rglob('*.py'):
        imports = _imports(path)
        assert not any(
            name == prefix or name.startswith(prefix + '.')
            for name in imports
            for prefix in ('src.app', 'src.logic', 'src.ui')
        ), path


def test_core_uses_diagnostics_instead_of_console_control_flow() -> None:
    for path in (SRC_ROOT / 'core').rglob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name):
                assert node.func.id not in {'print', 'input'}, f'{path}:{node.lineno}'
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == 'exit'
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == 'sys'
            ):
                pytest.fail(f'{path}:{node.lineno} calls sys.exit inside core')




def test_logic_does_not_use_console_control_flow() -> None:
    for path in (SRC_ROOT / 'logic').rglob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name):
                assert node.func.id not in {'print', 'input'}, f'{path}:{node.lineno}'
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == 'exit'
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == 'sys'
            ):
                pytest.fail(f'{path}:{node.lineno} calls sys.exit inside logic')


def test_operational_code_does_not_catch_base_exception() -> None:
    for path in SRC_ROOT.rglob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler) or node.type is None:
                continue
            if isinstance(node.type, ast.Name) and node.type.id == 'BaseException':
                pytest.fail(f'{path}:{node.lineno} catches BaseException')


def test_main_tab_ui_is_owned_by_tabs_package() -> None:
    tabs_root = SRC_ROOT / 'ui' / 'tabs'
    for tab_name in ('home', 'project', 'settings', 'tasks', 'tools', 'about', 'plugins'):
        assert (tabs_root / tab_name).is_dir(), tab_name
    assert not (SRC_ROOT / 'ui' / 'window_sections' / 'tabs.py').exists()
    assert not (SRC_ROOT / 'ui' / 'window_sections' / 'tabs_presenter.py').exists()


def test_logic_error_helper_does_not_own_localization_keys() -> None:
    logic_root = SRC_ROOT / 'logic' / 'help' / 'error_helper'
    for path in logic_root.rglob('*.py'):
        source = path.read_text(encoding='utf-8')
        assert 'error_helper_ext4_size_too_small_detail' not in source
        assert 'error_helper_ext4_size_too_small_solution' not in source
        assert 'error_helper_ext4_size_too_small_patterns' not in source
        assert 'load_rules_from_language_map' not in source

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
