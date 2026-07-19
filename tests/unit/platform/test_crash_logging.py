from __future__ import annotations

# Direct file execution bootstrap
import sys as _direct_sys
from pathlib import Path as _DirectPath

_DIRECT_PROJECT_ROOT = _DirectPath(__file__).resolve().parent
while _DIRECT_PROJECT_ROOT != _DIRECT_PROJECT_ROOT.parent:
    if (
        (_DIRECT_PROJECT_ROOT / 'src').is_dir()
        and (_DIRECT_PROJECT_ROOT / 'tests').is_dir()
        and (_DIRECT_PROJECT_ROOT / 'scripts').is_dir()
    ):
        break
    _DIRECT_PROJECT_ROOT = _DIRECT_PROJECT_ROOT.parent
else:
    raise RuntimeError(f'Project root was not found for {__file__}')

_direct_root_text = str(_DIRECT_PROJECT_ROOT)
if _direct_root_text not in _direct_sys.path:
    _direct_sys.path.insert(0, _direct_root_text)
if __package__ in {None, ''}:
    _direct_relative = _DirectPath(__file__).resolve().relative_to(
        _DIRECT_PROJECT_ROOT
    ).with_suffix('')
    __package__ = '.'.join(_direct_relative.parts[:-1])

import logging
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.platform import crash_logging


def _read_log(path: Path) -> str:
    crash_logging.flush_logging()
    return path.read_text(encoding='utf-8')


def test_early_logging_creates_runtime_layout_and_file(tmp_path: Path) -> None:
    log_path = tmp_path / 'logs' / 'startup.log'

    active = crash_logging.initialize_process_logging(
        tmp_path,
        log_path=log_path,
    )
    logging.getLogger('test.runtime').info('runtime layout ready')

    assert active == log_path.resolve()
    for relative_path in (
        'logs',
        'temp/plugins/downloads',
        'temp/plugins/runtime',
        'temp/updates',
        'temp/magisk',
        'temp/mtk_port',
        'plugins/installed',
    ):
        assert (tmp_path / relative_path).is_dir()

    content = _read_log(active)
    assert 'Logging initialized' in content
    assert 'runtime layout ready' in content
    assert 'test_crash_logging.py:' in content
    assert 'operation=process.startup' in content


def test_operation_context_logs_failure_with_traceback(tmp_path: Path) -> None:
    active = crash_logging.initialize_process_logging(
        tmp_path,
        log_path=tmp_path / 'logs' / 'operation.log',
    )

    with pytest.raises(RuntimeError, match='expected operation failure'):
        with crash_logging.operation_context('test.operation', source='unit'):
            raise RuntimeError('expected operation failure')

    content = _read_log(active)
    assert 'operation=test.operation' in content
    assert 'Operation started: source=' in content
    assert 'Operation failed after' in content
    assert 'RuntimeError: expected operation failure' in content


def test_tk_callback_exception_is_written_to_log(tmp_path: Path) -> None:
    active = crash_logging.initialize_process_logging(
        tmp_path,
        log_path=tmp_path / 'logs' / 'tk.log',
    )

    class FakeRoot:
        report_callback_exception = None

    root = FakeRoot()
    crash_logging.install_tk_exception_logging(root)

    try:
        raise ValueError('tk callback failure')
    except ValueError as error:
        assert root.report_callback_exception is not None
        root.report_callback_exception(type(error), error, error.__traceback__)

    content = _read_log(active)
    assert 'Unhandled exception captured from Tk callback' in content
    assert 'ValueError: tk callback failure' in content


def test_emergency_fallback_writes_traceback(tmp_path: Path) -> None:
    error = RuntimeError('fallback failure')
    path = crash_logging.write_emergency_fallback(
        tmp_path,
        phase='unit test',
        exception=error,
    )

    assert path == tmp_path / 'logs' / 'mio_emergency_startup.log'
    content = path.read_text(encoding='utf-8')
    assert 'phase=unit test' in content
    assert 'RuntimeError: fallback failure' in content


def test_background_system_exit_is_not_reported_as_crash(tmp_path: Path) -> None:
    active = crash_logging.initialize_process_logging(
        tmp_path,
        log_path=tmp_path / 'logs' / 'thread-system-exit.log',
    )
    error = SystemExit(0)

    crash_logging._thread_exception_hook(
        SimpleNamespace(
            exc_type=type(error),
            exc_value=error,
            exc_traceback=error.__traceback__,
            thread=None,
        )
    )

    content = _read_log(active)
    assert 'Unhandled exception captured' not in content
    assert 'SystemExit' not in content


if __name__ == '__main__':
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
