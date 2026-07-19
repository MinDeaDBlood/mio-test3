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
import subprocess
import sys
from pathlib import Path

from tests.support.paths import PROJECT_ROOT



REMOVED_COMPAT_MODULES = (
    'src/app/runtime_state.py',
    'src/app/runtime_accessors.py',
    'src/app/runtime_compat.py',
    'src/app/runtime/decorators.py',
    'src/app/localization_aliases.py',
    'src/app/tk_runtime.py',
    'src/core/utils.py',
    'src/ui/common/file_dialog_backend.py',
    'src/ui/common/window_redraw.py',
    'src/ui/tabs/plugins/module_dialogs.py',
    'src/ui/tabs/tools/download_firmware/window.py',
    'src/ui/tabs/plugins/_mpk_windows.py',
    'src/logic/projects/common/utils.py',
)

REMOVED_IMPORT_PREFIXES = (
    'src.app.runtime_state',
    'src.app.runtime_accessors',
    'src.app.runtime_compat',
    'src.app.runtime.decorators',
    'src.app.localization_aliases',
    'src.app.tk_runtime',
    'src.core.utils',
    'src.ui.common.file_dialog_backend',
    'src.ui.common.window_redraw',
    'src.ui.tabs.plugins.module_dialogs',
    'src.ui.tabs.tools.download_firmware.window',
    'src.ui.tabs.plugins._mpk_windows',
    'src.logic.projects.common.utils',
)


def _source_files() -> list[Path]:
    return sorted((PROJECT_ROOT / 'src').rglob('*.py'))


def _top_level_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding='utf-8'))
    modules: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_removed_compatibility_modules_stay_removed() -> None:
    for relative_path in REMOVED_COMPAT_MODULES:
        assert not (PROJECT_ROOT / relative_path).exists(), relative_path


def test_source_does_not_import_removed_compatibility_modules() -> None:
    violations: list[str] = []
    for path in _source_files():
        relative_path = path.relative_to(PROJECT_ROOT).as_posix()
        for module_name in _top_level_imports(path):
            if any(
                module_name == prefix or module_name.startswith(prefix + '.')
                for prefix in REMOVED_IMPORT_PREFIXES
            ):
                violations.append(f'{relative_path}: {module_name}')
    assert violations == []



def test_native_redraw_freeze_stays_removed() -> None:
    for source_file in _source_files():
        source = source_file.read_text(encoding='utf-8', errors='replace')
        assert 'WM_SETREDRAW' not in source
        assert 'suspend_window_redraw' not in source

def test_project_root_package_is_not_a_lazy_feature_facade() -> None:
    source = (PROJECT_ROOT / 'src/logic/projects/__init__.py').read_text(encoding='utf-8')
    assert 'def __getattr__' not in source
    assert '_DELEGATES' not in source
    assert '_EXPORTS' not in source
    assert 'import_module' not in source


def test_dialog_composition_boundary_keeps_tk_and_ui_imports_lazy() -> None:
    app_path = PROJECT_ROOT / 'src/app/composition/dialogs.py'
    app_source = app_path.read_text(encoding='utf-8')
    imports = _top_level_imports(app_path)

    assert not any(module == 'tkinter' or module.startswith('tkinter.') for module in imports)
    assert not any(module == 'src.ui' or module.startswith('src.ui.') for module in imports)
    assert "import_module('src.ui.warn.dialogs')" in app_source
    assert "import_module('src.app.composition.file_dialog')" in app_source

    script = (
        "import sys; "
        "import src.app.composition.dialogs; "
        "assert 'tkinter' not in sys.modules; "
        "assert 'src.ui.warn.dialogs' not in sys.modules; "
        "assert 'src.app.composition.file_dialog' not in sys.modules; "
        "print('APP_DIALOGS_LAZY_OK')"
    )
    proc = subprocess.run(
        [sys.executable, '-c', script],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        timeout=10,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert 'APP_DIALOGS_LAZY_OK' in proc.stdout


def test_file_dialog_and_geometry_live_only_in_ui_and_app_composition() -> None:
    assert not (PROJECT_ROOT / 'src/core/mkc_filedialog.py').exists()
    assert not (PROJECT_ROOT / 'src/core/ui_geometry.py').exists()
    assert not (PROJECT_ROOT / 'src/ui/common/file_dialog_backend.py').exists()

    dialog_source = (PROJECT_ROOT / 'src/ui/common/mkc_filedialog.py').read_text(encoding='utf-8')
    geometry_source = (PROJECT_ROOT / 'src/ui/common/geometry.py').read_text(encoding='utf-8')
    composition_source = (PROJECT_ROOT / 'src/app/composition/file_dialog.py').read_text(encoding='utf-8')

    assert 'class FileSelectionDialog' in dialog_source
    assert 'class DirectorySelectionDialog' in dialog_source
    assert 'def move_center' in geometry_source
    assert 'src.ui.common.mkc_filedialog' in composition_source

    for source_file in _source_files():
        source = source_file.read_text(encoding='utf-8', errors='replace')
        assert 'src.core.mkc_filedialog' not in source
        assert 'src.core.ui_geometry' not in source


def test_project_pack_receives_ui_prompts_instead_of_importing_ui() -> None:
    app_path = PROJECT_ROOT / 'src/app/project_pack.py'
    source = app_path.read_text(encoding='utf-8')
    imports = _top_level_imports(app_path)

    assert not any(module == 'tkinter' or module.startswith('tkinter.') for module in imports)
    assert not any(module == 'src.ui' or module.startswith('src.ui.') for module in imports)
    assert 'prompt_hybrid_option: HybridOptionPrompt' in source
    assert 'prompt_target_device: TargetDevicePrompt' in source


def test_unpack_registry_keeps_payload_dependencies_lazy() -> None:
    script = r"""
import sys
from src.logic.projects.unpack import registry
assert 'payload' in registry.get_available_formats()
assert 'src.core.payload_manifest' not in sys.modules
assert 'src.core.update_metadata_pb2' not in sys.modules
assert not any(name.startswith('google') for name in sys.modules)
result = registry.run_unpack(
    'payload',
    ['system'],
    unpack_func=lambda selected, format_name: (list(selected), format_name),
)
assert result == (['system'], 'payload')
assert 'src.core.payload_manifest' not in sys.modules
assert 'src.core.update_metadata_pb2' not in sys.modules
assert not any(name.startswith('google') for name in sys.modules)
print('UNPACK_REGISTRY_LAZY_OK')
"""
    proc = subprocess.run(
        [sys.executable, '-c', script],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        timeout=15,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert 'UNPACK_REGISTRY_LAZY_OK' in proc.stdout


def test_app_ui_imports_exist_only_at_composition_boundaries() -> None:
    violations: list[str] = []
    for path in sorted((PROJECT_ROOT / 'src/app').rglob('*.py')):
        relative_path = path.relative_to(PROJECT_ROOT).as_posix()
        ui_imports = [
            module
            for module in _top_level_imports(path)
            if module == 'src.ui' or module.startswith('src.ui.')
        ]
        if not ui_imports:
            continue
        allowed = (
            relative_path == 'src/app/bootstrap.py'
            or relative_path.startswith('src/app/composition/')
        )
        if not allowed:
            violations.append(f'{relative_path}: {ui_imports}')
    assert violations == []

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
