from __future__ import annotations

import logging
import os
from pathlib import Path

from src.platform.crash_logging import (
    LOG_FORMAT,
    MIO_FILE_HANDLER_ATTR,
    MIO_FILE_HANDLER_PATH_ATTR,
    initialize_process_logging,
)

_TRUTHY_ENV_VALUES = {'1', 'true', 'yes', 'on'}


def configure_logging(*, development: bool, log_path: str) -> None:
    active_path = Path(log_path).expanduser().resolve()
    initialize_process_logging(
        active_path.parent.parent,
        development=development,
        log_path=active_path,
    )
    suppress_pillow_debug_noise()


def suppress_pillow_debug_noise() -> None:
    if os.environ.get('MIO_DEBUG_PIL_LOGS', '').strip().lower() in _TRUTHY_ENV_VALUES:
        return
    for logger_name in ('PIL', 'PIL.Image', 'PIL.PngImagePlugin'):
        logging.getLogger(logger_name).setLevel(logging.WARNING)


__all__ = [
    'LOG_FORMAT',
    'MIO_FILE_HANDLER_ATTR',
    'MIO_FILE_HANDLER_PATH_ATTR',
    'configure_logging',
    'suppress_pillow_debug_noise',
]
