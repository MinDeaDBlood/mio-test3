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


from threading import Event

from src.app.animated_tasks import AnimatedTaskRunner
from src.app.operation_gate import OperationBusyError, OperationGate
from src.app.ui_tasks import UiTaskRunner


class _Dispatcher:
    def dispatch(self, callback, *args):
        return callback(*args)


class _Animation:
    def __init__(self):
        self.master = None
        self.started = 0
        self.stopped = 0

    def start(self, frame_index: int = 0):
        self.started += 1
        return frame_index

    def stop(self):
        self.stopped += 1

    def initialize(self):
        return None

    def load_gif(self, _gif):
        return None


class _Scheduler:
    def __init__(self):
        self.callbacks = []

    def after(self, _delay, callback):
        self.callbacks.append(callback)


def test_ui_task_runner_passes_worker_keyword_arguments() -> None:
    completed = []
    runner = UiTaskRunner(
        dispatcher=_Dispatcher(),
        start_worker=lambda callback, *, daemon=True: callback(),
        operation_gate=OperationGate(),
    )

    started = runner.run(
        lambda *, value, scale: value * scale,
        worker_kwargs={'value': 7, 'scale': 6},
        on_success=completed.append,
    )

    assert started is None
    assert completed == [42]


def test_ui_task_runner_delivers_real_worker_exception_and_finalizes_closed_view() -> None:
    errors = []
    finalized = []
    runner = UiTaskRunner(
        dispatcher=_Dispatcher(),
        is_alive=lambda: False,
        start_worker=lambda callback, *, daemon=True: callback(),
        operation_gate=OperationGate(),
    )

    runner.run(
        lambda: (_ for _ in ()).throw(ValueError('broken worker')),
        on_error=errors.append,
        on_finally=lambda: finalized.append(True),
    )

    assert errors == []
    assert finalized == [True]


def test_exclusive_ui_tasks_reject_second_operation_and_release_after_completion() -> None:
    gate = OperationGate()
    pending = []
    first = UiTaskRunner(
        dispatcher=_Dispatcher(),
        start_worker=lambda callback, *, daemon=True: pending.append(callback),
        operation_gate=gate,
    )
    second_errors = []
    second_finalized = []
    second = UiTaskRunner(
        dispatcher=_Dispatcher(),
        start_worker=lambda callback, *, daemon=True: callback(),
        operation_gate=gate,
    )

    assert first.run(lambda: 'done', exclusive=True) is None
    assert second.run(
        lambda: 'must not run',
        on_error=second_errors.append,
        on_finally=lambda: second_finalized.append(True),
        exclusive=True,
    ) is False
    assert isinstance(second_errors[0], OperationBusyError)
    assert second_finalized == [True]

    pending.pop()()
    assert second.run(lambda: 'now runs', exclusive=True) is None


def test_animated_task_runner_allows_only_one_heavy_operation() -> None:
    gate = OperationGate()
    animation = _Animation()
    scheduler = _Scheduler()
    animation.master = scheduler
    runner = AnimatedTaskRunner(animation, operation_gate=gate)
    release = Event()

    @runner
    def first_task():
        release.wait(timeout=2)

    @runner
    def second_task():
        raise AssertionError('second task must not start')

    assert first_task() is None
    assert second_task() is False
    release.set()
    while scheduler.callbacks:
        scheduler.callbacks.pop(0)()
    assert runner.has_tasks() is False
    assert animation.started == 1
    assert animation.stopped == 1

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
