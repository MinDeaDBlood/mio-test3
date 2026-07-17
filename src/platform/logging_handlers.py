"""Logging handler construction shared by early and regular startup."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from src.platform.operation_logging import OPERATION_FILTER

LOG_FORMAT = (
    '%(asctime)s.%(msecs)03d | %(levelname)-8s | pid=%(process)d | '
    'thread=%(threadName)s | %(name)s | %(filename)s:%(lineno)d | '
    'operation=%(operation)s | op_id=%(operation_id)s | %(message)s'
)
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
MIO_FILE_HANDLER_ATTR = '_mio_kitchen_tool_log_handler'
MIO_FILE_HANDLER_PATH_ATTR = '_mio_kitchen_tool_log_path'


def find_mio_file_handler(root_logger: logging.Logger) -> logging.Handler | None:
    for handler in root_logger.handlers:
        if hasattr(handler, MIO_FILE_HANDLER_ATTR) and bool(
            getattr(handler, MIO_FILE_HANDLER_ATTR)
        ):
            return handler
    return None


def file_handler_path(handler: logging.FileHandler) -> Path | None:
    if not hasattr(handler, 'baseFilename'):
        return None
    value = handler.baseFilename
    return Path(value).expanduser().resolve() if value else None


def file_handler_uses_utf8(handler: logging.FileHandler) -> bool:
    encoding = handler.encoding
    if encoding is None and handler.stream is not None:
        encoding = handler.stream.encoding
    if encoding is None:
        return False
    return encoding.lower().replace('-', '').replace('_', '') == 'utf8'


def find_reusable_file_handler(
    root_logger: logging.Logger, log_path: Path
) -> logging.FileHandler | None:
    reusable: logging.FileHandler | None = None
    for handler in list(root_logger.handlers):
        if not isinstance(handler, logging.FileHandler):
            continue
        if file_handler_path(handler) != log_path:
            continue
        if reusable is None and file_handler_uses_utf8(handler):
            reusable = handler
            continue
        root_logger.removeHandler(handler)
        handler.close()
    return reusable


def configure_handler(handler: logging.Handler, log_path: Path) -> None:
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
    handler.addFilter(OPERATION_FILTER)
    setattr(handler, MIO_FILE_HANDLER_ATTR, True)
    setattr(handler, MIO_FILE_HANDLER_PATH_ATTR, str(log_path))


def ensure_console_handler(root_logger: logging.Logger) -> None:
    for handler in root_logger.handlers:
        if hasattr(handler, '_mio_kitchen_console_handler') and bool(
            getattr(handler, '_mio_kitchen_console_handler')
        ):
            return
    console_handler = logging.StreamHandler(stream=sys.__stderr__)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(
        logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    )
    console_handler.addFilter(OPERATION_FILTER)
    setattr(console_handler, '_mio_kitchen_console_handler', True)
    root_logger.addHandler(console_handler)


__all__ = [
    'LOG_DATE_FORMAT',
    'LOG_FORMAT',
    'MIO_FILE_HANDLER_ATTR',
    'MIO_FILE_HANDLER_PATH_ATTR',
    'configure_handler',
    'ensure_console_handler',
    'file_handler_path',
    'file_handler_uses_utf8',
    'find_mio_file_handler',
    'find_reusable_file_handler',
]
