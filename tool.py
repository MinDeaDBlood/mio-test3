#!/usr/bin/env python3
from __future__ import annotations

import logging
import os
import sys
import tempfile
import time
import traceback
from pathlib import Path
from types import TracebackType


def _resolve_root() -> Path:
    if getattr(sys, 'frozen', False):
        executable_parent = Path(sys.executable).resolve().parent
        if (
            sys.platform == 'darwin'
            and executable_parent.name == 'MacOS'
            and executable_parent.parent.name == 'Contents'
            and executable_parent.parent.parent.suffix == '.app'
        ):
            return executable_parent.parent.parent.parent
        return executable_parent
    return Path(__file__).resolve().parent


PROJECT_ROOT = _resolve_root()


def _bootstrap_log_directories() -> tuple[Path, ...]:
    candidates = [PROJECT_ROOT / 'logs']
    local_app_data = os.environ.get('LOCALAPPDATA')
    if local_app_data:
        candidates.append(Path(local_app_data) / 'MIO-KITCHEN' / 'logs')
    candidates.append(Path(tempfile.gettempdir()) / 'MIO-KITCHEN' / 'logs')
    unique: list[Path] = []
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if resolved not in unique:
            unique.append(resolved)
    return tuple(unique)


def _create_bootstrap_log() -> Path | None:
    timestamp = time.strftime('%Y%m%d_%H-%M-%S', time.localtime())
    filename = f'mio_{timestamp}_pid-{os.getpid()}_bootstrap.log'
    for log_dir in _bootstrap_log_directories():
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            path = log_dir / filename
            with path.open('a', encoding='utf-8', buffering=1) as stream:
                stream.write(
                    f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] '
                    f'bootstrap entered executable={sys.executable!r} '
                    f'cwd={os.getcwd()!r} root={str(PROJECT_ROOT)!r}\n'
                )
                stream.flush()
            return path
        except OSError:
            continue
    return None


def _bootstrap_note(message: str) -> None:
    if _ACTIVE_LOG_PATH is None:
        return
    try:
        with _ACTIVE_LOG_PATH.open('a', encoding='utf-8', buffering=1) as stream:
            stream.write(
                f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] {message}\n'
            )
            stream.flush()
    except OSError:
        return


_ACTIVE_LOG_PATH: Path | None = _create_bootstrap_log()
if _ACTIVE_LOG_PATH is not None:
    os.environ['MIO_ACTIVE_LOG_PATH'] = str(_ACTIVE_LOG_PATH)


def _write_local_emergency(phase: str, exception: BaseException) -> Path | None:
    try:
        if _ACTIVE_LOG_PATH is not None:
            fallback_path = _ACTIVE_LOG_PATH
        else:
            log_dir = PROJECT_ROOT / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            fallback_path = log_dir / 'mio_emergency_startup.log'
        with fallback_path.open('a', encoding='utf-8') as stream:
            stream.write(f'\n[{time.strftime("%Y-%m-%d %H:%M:%S")}] phase={phase}\n')
            traceback.print_exception(
                type(exception),
                exception,
                exception.__traceback__,
                file=stream,
            )
            stream.flush()
        return fallback_path
    except Exception:
        return None


def _show_fatal_startup_message(log_path: Path | None) -> None:
    message = 'MIO Kitchen could not start.'
    if log_path is not None:
        message += f'\n\nDiagnostic log:\n{log_path}'
    try:
        from tkinter import Tk, messagebox

        root = Tk()
        root.withdraw()
        messagebox.showerror('MIO Kitchen startup error', message, parent=root)
        root.destroy()
    except Exception:
        return


def _record_fatal_error(
    phase: str,
    exception: BaseException,
    trace: TracebackType | None = None,
) -> Path | None:
    global _ACTIVE_LOG_PATH
    try:
        from src.platform.crash_logging import flush_logging, write_emergency_fallback

        logging.getLogger('mio.crash').critical(
            'Fatal application error during %s',
            phase,
            exc_info=(type(exception), exception, trace or exception.__traceback__),
        )
        flush_logging()
        if _ACTIVE_LOG_PATH is not None:
            return _ACTIVE_LOG_PATH
        return write_emergency_fallback(
            PROJECT_ROOT,
            phase=phase,
            exception=exception,
        )
    except Exception:
        return _write_local_emergency(phase, exception)


def _initialize_logging() -> None:
    global _ACTIVE_LOG_PATH
    try:
        from src.platform.crash_logging import (
            initialize_process_logging,
            log_startup_phase,
            start_startup_watchdog,
        )

        _bootstrap_note('loading structured logging')
        _ACTIVE_LOG_PATH = initialize_process_logging(
            PROJECT_ROOT,
            log_path=_ACTIVE_LOG_PATH,
        )
        log_startup_phase('tool.entrypoint.loaded')
        start_startup_watchdog()
    except BaseException as exception:
        fallback = _record_fatal_error('logging initialization', exception)
        _show_fatal_startup_message(fallback)
        raise SystemExit(1) from exception


_initialize_logging()
_bootstrap_note('structured logging initialized')

if sys.version_info < (3, 10):
    error = RuntimeError(
        f'Unsupported Python version: {sys.version}. Python 3.10 or newer is required.'
    )
    log_path = _record_fatal_error('python version validation', error)
    _show_fatal_startup_message(log_path)
    raise SystemExit(1)

try:
    from src.platform.crash_logging import log_startup_phase

    log_startup_phase('application import started')
    _bootstrap_note('application import started')
    from src.app.entrypoint import init
    log_startup_phase('application import completed')
    _bootstrap_note('application import completed')
except BaseException as exception:
    log_path = _record_fatal_error('application import', exception)
    _show_fatal_startup_message(log_path)
    time.sleep(1)
    raise SystemExit(1) from exception


if __name__ == '__main__':
    try:
        log_startup_phase('application runtime started')
        init(sys.argv)
        logging.getLogger('mio.lifecycle').info('Application runtime returned normally')
    except SystemExit as exception:
        exit_code = exception.code if isinstance(exception.code, int) else 1
        logging.getLogger('mio.lifecycle').info(
            'Application requested SystemExit with code %s',
            exit_code,
        )
        raise
    except BaseException as exception:
        log_path = _record_fatal_error('application runtime', exception)
        _show_fatal_startup_message(log_path)
        raise SystemExit(1) from exception
