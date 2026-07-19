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
def _top_level_import_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding='utf-8'))
    modules: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
        elif isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
    return modules


def _source_files(layer: str) -> list[Path]:
    return sorted((PROJECT_ROOT / 'src' / layer).rglob('*.py'))


def _relative(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def test_ui_package_initializers_do_not_eagerly_import_windows() -> None:
    violations: list[str] = []
    for path in sorted((PROJECT_ROOT / 'src/ui').rglob('__init__.py')):
        for module in _top_level_import_modules(path):
            if module.endswith('.window') or module.endswith('.view'):
                violations.append(f'{_relative(path)}: {module}')
    assert violations == []


def test_ui_does_not_import_workflow_services_or_low_level_execution_modules() -> None:
    forbidden_exact = {
        'subprocess',
        'threading',
        'shutil',
        'zipfile',
        'src.core.process_runner',
        'src.logic.network_downloads',
    }
    forbidden_suffixes = ('.service', '.controller', '.orchestrator', '.use_case')
    allowed_logic_model_fragments = ('.models', '.package_reader', '.messages')

    violations: list[str] = []
    for path in _source_files('ui'):
        for module in _top_level_import_modules(path):
            if module in forbidden_exact:
                violations.append(f'{_relative(path)}: {module}')
                continue
            if module.startswith('src.logic.') and module.endswith(forbidden_suffixes):
                if not any(fragment in module for fragment in allowed_logic_model_fragments):
                    violations.append(f'{_relative(path)}: {module}')
    assert violations == []


def test_logic_and_core_do_not_import_ui_or_application_layers() -> None:
    violations: list[str] = []
    for layer in ('logic', 'core'):
        for path in _source_files(layer):
            for module in _top_level_import_modules(path):
                if module == 'src.ui' or module.startswith('src.ui.'):
                    violations.append(f'{_relative(path)}: {module}')
                if module == 'src.app' or module.startswith('src.app.'):
                    violations.append(f'{_relative(path)}: {module}')
                if module == 'tkinter' or module.startswith('tkinter.'):
                    violations.append(f'{_relative(path)}: {module}')
    assert violations == []


def test_runtime_and_workflow_builders_are_not_stored_in_ui() -> None:
    forbidden_names = {
        'runtime_context.py',
        'composition.py',
        'session.py',
        'fetch_flow.py',
        'install_flow.py',
        'uninstall_flow.py',
    }
    violations = [
        _relative(path)
        for path in _source_files('ui')
        if path.name in forbidden_names
    ]
    assert violations == []


def test_removed_heavy_and_compatibility_surfaces_stay_removed() -> None:
    removed_paths = (
        'src/ui/common/loading.py',
        'src/ui/tabs/project/common.py',
        'src/ui/tabs/project/convert/actions.py',
        'src/ui/tabs/project/pack/hybrid/window.py',
        'src/ui/bug_report/submit/action.py',
        'src/ui/tabs/tools/download_firmware/controller.py',
        'src/core/utils.py',
        'src/core/localization.py',
        'src/core/runtime_flags.py',
        'src/core/images.py',
        'src/core/miside_banner.py',
        'src/app/runtime_state.py',
        'src/app/runtime_accessors.py',
        'src/app/runtime_compat.py',
        'src/app/tk_runtime.py',
    )
    for relative_path in removed_paths:
        assert not (PROJECT_ROOT / relative_path).exists(), relative_path


def test_application_async_boundary_stays_in_app() -> None:
    background_imports = _top_level_import_modules(PROJECT_ROOT / 'src/app/background_jobs.py')
    task_imports = _top_level_import_modules(PROJECT_ROOT / 'src/app/ui_tasks.py')

    assert 'threading' in background_imports
    assert 'src.app.background_jobs' in task_imports
    assert not (PROJECT_ROOT / 'src/logic/common/ui_tasks.py').exists()
    assert not (PROJECT_ROOT / 'src/logic/common/ui_feedback.py').exists()


def run_all() -> None:
    test_ui_package_initializers_do_not_eagerly_import_windows()
    test_ui_does_not_import_workflow_services_or_low_level_execution_modules()
    test_logic_and_core_do_not_import_ui_or_application_layers()
    test_runtime_and_workflow_builders_are_not_stored_in_ui()
    test_removed_heavy_and_compatibility_surfaces_stay_removed()
    test_application_async_boundary_stays_in_app()


def test_lazy_heavy_surface_cleanup_contract() -> None:
    run_all()

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
