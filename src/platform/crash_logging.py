"""Process wide logging and crash capture for the earliest startup stage."""
from __future__ import annotations

import atexit
import faulthandler
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import platform
import sys
from threading import ExceptHookArgs
import time
from types import TracebackType
from typing import Any, TextIO

from src.platform.emergency_logging import write_emergency_fallback
from src.platform.logging_handlers import (
    LOG_DATE_FORMAT,
    LOG_FORMAT,
    MIO_FILE_HANDLER_ATTR,
    MIO_FILE_HANDLER_PATH_ATTR,
    configure_handler,
    file_handler_uses_utf8,
    ensure_console_handler,
    find_mio_file_handler,
    find_reusable_file_handler,
)
from src.platform.operation_logging import (
    DEFAULT_OPERATION,
    current_operation,
    operation_context,
    render_details,
    reset_current_operation,
    set_current_operation,
)
from src.platform.startup_watchdog import start_watchdog, stop_watchdog
from uuid import uuid4

ACTIVE_LOG_PATH_ENV = 'MIO_ACTIVE_LOG_PATH'
MAX_LOG_BYTES = 10 * 1024 * 1024
LOG_BACKUP_COUNT = 3
MAX_RETAINED_RUN_LOGS = 50
STARTUP_WATCHDOG_SECONDS = 30

_RUNTIME_DIRECTORIES = (
    'logs',
    'temp',
    'temp/plugins',
    'temp/plugins/downloads',
    'temp/plugins/runtime',
    'temp/updates',
    'temp/magisk',
    'temp/mtk_port',
    'plugins',
    'plugins/installed',
)
_ACTIVE_LOG_PATH: Path | None = None
_FAULT_STREAM: TextIO | None = None
_FAULT_STREAM_PATH: Path | None = None
_HOOKS_INSTALLED = False
_EXIT_RECORDED = False
def resolve_process_root() -> Path:
    """Resolve the writable portable application root for source and frozen runs."""
    is_frozen = bool(sys.frozen) if hasattr(sys, 'frozen') else False
    if is_frozen:
        executable_parent = Path(sys.executable).resolve().parent
        if (
            platform.system() == 'Darwin'
            and executable_parent.name == 'MacOS'
            and executable_parent.parent.name == 'Contents'
            and executable_parent.parent.parent.suffix == '.app'
        ):
            return executable_parent.parent.parent.parent
        return executable_parent
    return Path(__file__).resolve().parents[2]


def ensure_runtime_layout(project_root: str | os.PathLike[str]) -> tuple[Path, ...]:
    root = Path(project_root).resolve()
    created: list[Path] = []
    for relative_path in _RUNTIME_DIRECTORIES:
        directory = root / relative_path
        directory.mkdir(parents=True, exist_ok=True)
        created.append(directory)
    return tuple(created)


def _new_log_path(log_dir: Path) -> Path:
    timestamp = time.strftime('%Y%m%d_%H-%M-%S', time.localtime())
    suffix = uuid4().hex[:8]
    return log_dir / f'mio_{timestamp}_pid-{os.getpid()}_{suffix}.log'


def _normalized_path(value: str | os.PathLike[str]) -> Path:
    return Path(value).expanduser().resolve()


def _prune_old_logs(log_dir: Path, active_log: Path) -> None:
    candidates = sorted(
        (
            path
            for path in log_dir.glob('mio_*.log*')
            if path.is_file() and path != active_log
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for stale_path in candidates[MAX_RETAINED_RUN_LOGS:]:
        try:
            stale_path.unlink()
        except OSError:
            continue


def _enable_faulthandler(log_path: Path) -> None:
    global _FAULT_STREAM, _FAULT_STREAM_PATH
    if _FAULT_STREAM is not None and _FAULT_STREAM_PATH == log_path:
        return
    if _FAULT_STREAM is not None:
        try:
            faulthandler.disable()
        except RuntimeError:
            pass
        try:
            _FAULT_STREAM.close()
        except OSError:
            pass
        _FAULT_STREAM = None
        _FAULT_STREAM_PATH = None
    try:
        _FAULT_STREAM = log_path.open('a', encoding='utf-8', buffering=1)
        _FAULT_STREAM_PATH = log_path
        faulthandler.enable(file=_FAULT_STREAM, all_threads=True)
    except (OSError, RuntimeError):
        _FAULT_STREAM = None
        _FAULT_STREAM_PATH = None


def _flush_handlers() -> None:
    for handler in logging.getLogger().handlers:
        try:
            handler.flush()
        except Exception:
            continue
    if _FAULT_STREAM is not None:
        try:
            _FAULT_STREAM.flush()
        except Exception:
            pass


def flush_logging() -> None:
    _flush_handlers()


def start_startup_watchdog(timeout_seconds: int = STARTUP_WATCHDOG_SECONDS) -> bool:
    started = start_watchdog(_FAULT_STREAM, timeout_seconds)
    _flush_handlers()
    return started


def stop_startup_watchdog() -> None:
    stop_watchdog()
    _flush_handlers()


def _log_uncaught_exception(
    exception_type: type[BaseException],
    exception: BaseException,
    trace: TracebackType | None,
    *,
    origin: str,
) -> None:
    logging.getLogger('mio.crash').critical(
        'Unhandled exception captured from %s',
        origin,
        exc_info=(exception_type, exception, trace),
    )
    _flush_handlers()


def _main_exception_hook(
    exception_type: type[BaseException],
    exception: BaseException,
    trace: TracebackType | None,
) -> None:
    if issubclass(exception_type, KeyboardInterrupt):
        sys.__excepthook__(exception_type, exception, trace)
        return
    _log_uncaught_exception(
        exception_type,
        exception,
        trace,
        origin='main thread',
    )


def _thread_exception_hook(args: ExceptHookArgs) -> None:
    if issubclass(args.exc_type, SystemExit):
        return
    thread_name = args.thread.name if args.thread is not None else '<unknown>'
    _log_uncaught_exception(
        args.exc_type,
        args.exc_value,
        args.exc_traceback,
        origin=f'background thread {thread_name}',
    )


def _unraisable_exception_hook(args: sys.UnraisableHookArgs) -> None:
    exception = args.exc_value or RuntimeError(args.err_msg or 'Unraisable exception')
    exception_type = args.exc_type or type(exception)
    _log_uncaught_exception(
        exception_type,
        exception,
        args.exc_traceback,
        origin=f'unraisable object {args.object!r}',
    )


def _record_process_exit() -> None:
    global _EXIT_RECORDED
    if _EXIT_RECORDED:
        return
    _EXIT_RECORDED = True
    logging.getLogger('mio.lifecycle').info('Process exit requested')
    _flush_handlers()


def _install_process_hooks() -> None:
    global _HOOKS_INSTALLED
    if _HOOKS_INSTALLED:
        return
    _HOOKS_INSTALLED = True
    sys.excepthook = _main_exception_hook
    if hasattr(sys, 'unraisablehook'):
        sys.unraisablehook = _unraisable_exception_hook
    try:
        import threading

        threading.excepthook = _thread_exception_hook
    except (AttributeError, ImportError):
        pass
    atexit.register(_record_process_exit)


def initialize_process_logging(
    project_root: str | os.PathLike[str] | None = None,
    *,
    development: bool = False,
    log_path: str | os.PathLike[str] | None = None,
) -> Path:
    """Create runtime directories and install the process wide file logger."""
    global _ACTIVE_LOG_PATH

    root = _normalized_path(project_root or resolve_process_root())
    ensure_runtime_layout(root)
    requested_path = log_path or os.environ.get(ACTIVE_LOG_PATH_ENV)
    active_log = (
        _normalized_path(requested_path)
        if requested_path
        else _new_log_path(root / 'logs')
    )
    active_log.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    existing_handler = find_mio_file_handler(root_logger)
    existing_path = None
    if existing_handler is not None:
        if hasattr(existing_handler, MIO_FILE_HANDLER_PATH_ATTR):
            existing_path_value = getattr(
                existing_handler, MIO_FILE_HANDLER_PATH_ATTR
            )
        elif hasattr(existing_handler, 'baseFilename'):
            existing_path_value = existing_handler.baseFilename
        else:
            existing_path_value = None
        if existing_path_value:
            existing_path = _normalized_path(existing_path_value)

    if existing_handler is not None and (
        existing_path != active_log
        or not isinstance(existing_handler, logging.FileHandler)
        or not file_handler_uses_utf8(existing_handler)
    ):
        root_logger.removeHandler(existing_handler)
        try:
            existing_handler.close()
        except Exception:
            pass
        existing_handler = None

    if existing_handler is None:
        existing_handler = find_reusable_file_handler(root_logger, active_log)

    if existing_handler is None:
        existing_handler = RotatingFileHandler(
            active_log,
            mode='a',
            maxBytes=MAX_LOG_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8',
            delay=False,
        )
        root_logger.addHandler(existing_handler)
    configure_handler(existing_handler, active_log)

    if development:
        ensure_console_handler(root_logger)

    _ACTIVE_LOG_PATH = active_log
    os.environ[ACTIVE_LOG_PATH_ENV] = str(active_log)
    logging.captureWarnings(True)
    _enable_faulthandler(active_log)
    _install_process_hooks()
    _prune_old_logs(active_log.parent, active_log)

    logger = logging.getLogger('mio.startup')
    logger.info('Logging initialized: %s', active_log)
    logger.info(
        'Process environment: python=%s platform=%s machine=%s frozen=%s',
        platform.python_version(),
        platform.platform(),
        platform.machine(),
        bool(sys.frozen) if hasattr(sys, 'frozen') else False,
    )
    logger.info(
        'Process paths: executable=%s cwd=%s project_root=%s argv=%r',
        sys.executable,
        os.getcwd(),
        root,
        sys.argv,
    )
    logger.debug('Runtime directories: %s', ', '.join(_RUNTIME_DIRECTORIES))
    _flush_handlers()
    return active_log


def get_active_log_path() -> Path | None:
    if _ACTIVE_LOG_PATH is not None:
        return _ACTIVE_LOG_PATH
    environment_path = os.environ.get(ACTIVE_LOG_PATH_ENV)
    if environment_path:
        return _normalized_path(environment_path)
    return None


def log_startup_phase(phase: str, **details: Any) -> None:
    detail_text = render_details(details)
    logging.getLogger('mio.startup').info(
        'Startup phase: %s%s',
        phase,
        f' | {detail_text}' if detail_text else '',
    )
    _flush_handlers()


def install_tk_exception_logging(root_window: Any) -> None:
    """Route uncaught Tk callback failures into the process crash log."""

    def report_callback_exception(
        exception_type: type[BaseException],
        exception: BaseException,
        trace: TracebackType | None,
    ) -> None:
        _log_uncaught_exception(
            exception_type,
            exception,
            trace,
            origin='Tk callback',
        )

    root_window.report_callback_exception = report_callback_exception
    logging.getLogger('mio.startup').debug('Tk exception hook installed')


__all__ = [
    'ACTIVE_LOG_PATH_ENV',
    'DEFAULT_OPERATION',
    'LOG_DATE_FORMAT',
    'LOG_FORMAT',
    'MIO_FILE_HANDLER_ATTR',
    'MIO_FILE_HANDLER_PATH_ATTR',
    'current_operation',
    'ensure_runtime_layout',
    'flush_logging',
    'get_active_log_path',
    'initialize_process_logging',
    'install_tk_exception_logging',
    'log_startup_phase',
    'operation_context',
    'reset_current_operation',
    'resolve_process_root',
    'set_current_operation',
    'start_startup_watchdog',
    'stop_startup_watchdog',
    'write_emergency_fallback',
]
