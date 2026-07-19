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


def test_ui_views_do_not_construct_background_execution_infrastructure() -> None:
    forbidden = {
        'src.app.ui_tasks',
        'src.app.ui_feedback',
        'src.app.background_jobs',
        'threading',
    }
    violations: list[str] = []
    for path in sorted((PROJECT_ROOT / 'src/ui').rglob('*.py')):
        imports = _top_level_import_modules(path)
        matched = sorted(imports & forbidden)
        if matched:
            violations.append(f"{path.relative_to(PROJECT_ROOT).as_posix()}: {matched}")
    assert violations == []


def test_application_composition_builds_ui_task_runners() -> None:
    expected_boundaries = (
        'src/app/composition/file_dialog.py',
        'src/app/composition/editor.py',
        'src/app/composition/convert.py',
        'src/app/composition/update.py',
        'src/app/composition/merge_super.py',
        'src/app/composition/download_firmware.py',
    )
    for relative_path in expected_boundaries:
        imports = _top_level_import_modules(PROJECT_ROOT / relative_path)
        assert 'src.app.ui_tasks' in imports, relative_path
        assert 'src.app.ui_feedback' in imports, relative_path


def test_ui_task_runner_dispatches_completion_back_to_ui_boundary() -> None:
    from src.app.ui_tasks import UiTaskRunner

    dispatched: list[object] = []
    completed: list[object] = []

    class Dispatcher:
        def dispatch(self, callback, *args):
            dispatched.append(callback)
            return callback(*args)

    def start_worker(callback, *, daemon=True):
        assert daemon is True
        callback()

    runner = UiTaskRunner(
        dispatcher=Dispatcher(),
        is_alive=lambda: True,
        start_worker=start_worker,
    )
    runner.run(lambda value: value * 2, 21, on_success=completed.append)

    assert len(dispatched) == 1
    assert completed == [42]


def test_ui_task_runner_does_not_update_closed_views() -> None:
    from src.app.ui_tasks import UiTaskRunner

    completed: list[object] = []

    class Dispatcher:
        def dispatch(self, callback, *args):
            return callback(*args)

    runner = UiTaskRunner(
        dispatcher=Dispatcher(),
        is_alive=lambda: False,
        start_worker=lambda callback, *, daemon=True: callback(),
    )
    runner.run(lambda: 'done', on_success=completed.append)

    assert completed == []


def run_all() -> None:
    test_ui_views_do_not_construct_background_execution_infrastructure()
    test_application_composition_builds_ui_task_runners()
    test_ui_task_runner_dispatches_completion_back_to_ui_boundary()
    test_ui_task_runner_does_not_update_closed_views()


def test_ui_task_runner_adoption_contract() -> None:
    run_all()

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
