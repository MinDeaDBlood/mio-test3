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


def test_mkc_file_dialog_uses_application_async_boundary() -> None:
    view_source = (PROJECT_ROOT / 'src/ui/common/mkc_filedialog.py').read_text(encoding='utf-8')
    composition_source = (PROJECT_ROOT / 'src/app/composition/file_dialog.py').read_text(encoding='utf-8')
    assert 'build_ui_dispatcher' not in view_source
    assert 'build_ui_task_runner' not in view_source
    assert 'from src.app.ui_feedback import build_ui_dispatcher' in composition_source
    assert 'from src.app.ui_tasks import build_ui_task_runner' in composition_source
    assert 'src.logic.common.ui_feedback' not in composition_source
    assert 'src.logic.common.ui_tasks' not in composition_source


def test_application_async_boundary_stays_out_of_logic() -> None:
    feedback_source = (PROJECT_ROOT / 'src/app/ui_feedback.py').read_text(encoding='utf-8')
    tasks_source = (PROJECT_ROOT / 'src/app/ui_tasks.py').read_text(encoding='utf-8')
    assert 'class UiDispatcher' in feedback_source
    assert 'class UiTaskRunner' in tasks_source
    assert 'start_background_job' in tasks_source
    assert not (PROJECT_ROOT / 'src/logic/common/ui_feedback.py').exists()
    assert not (PROJECT_ROOT / 'src/logic/common/ui_tasks.py').exists()
    assert not (PROJECT_ROOT / 'src/ui/common/async_boundary.py').exists()


def test_application_async_boundary_top_level_imports_stay_narrow() -> None:
    assert _top_level_import_modules(PROJECT_ROOT / 'src/app/ui_tasks.py') <= {
        '__future__',
        'logging',
        'collections.abc',
        'dataclasses',
        'typing',
        'src.app.background_jobs',
        'src.app.operation_gate',
        'src.app.ui_feedback',
        'src.core.contracts',
    }


def run_all() -> None:
    test_mkc_file_dialog_uses_application_async_boundary()
    test_application_async_boundary_stays_out_of_logic()
    test_application_async_boundary_top_level_imports_stay_narrow()


if __name__ == '__main__':
    run_all()
    print('FILE_DIALOG_ASYNC_BOUNDARY_TESTS_OK')
