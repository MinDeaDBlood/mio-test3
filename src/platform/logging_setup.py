from __future__ import annotations

import logging
import os


LOG_FORMAT = '%(levelname)s:%(asctime)s:%(filename)s:%(name)s:%(message)s'
MIO_FILE_HANDLER_ATTR = '_mio_kitchen_tool_log_handler'
MIO_FILE_HANDLER_PATH_ATTR = '_mio_kitchen_tool_log_path'
_TRUTHY_ENV_VALUES = {'1', 'true', 'yes', 'on'}


def configure_logging(*, development: bool, log_path: str) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    if development:
        if not root_logger.handlers:
            _install_development_console_logging(root_logger)
    else:
        _ensure_utf8_file_logging(root_logger, log_path)
    suppress_pillow_debug_noise()


def _ensure_utf8_file_logging(root_logger: logging.Logger, log_path: str) -> None:
    normalized_log_path = os.path.abspath(os.fspath(log_path))
    existing_handler = _find_existing_file_handler(root_logger, normalized_log_path)
    if existing_handler is not None and not _file_handler_uses_utf8(existing_handler):
        root_logger.removeHandler(existing_handler)
        existing_handler.close()
        existing_handler = None
    if existing_handler is None:
        existing_handler = logging.FileHandler(normalized_log_path, mode='w', encoding='utf-8')
        root_logger.addHandler(existing_handler)
    _configure_mio_file_handler(existing_handler, normalized_log_path)


def _find_existing_file_handler(
    root_logger: logging.Logger,
    normalized_log_path: str,
) -> logging.FileHandler | None:
    for handler in root_logger.handlers:
        if not isinstance(handler, logging.FileHandler):
            continue
        handler_path = (
            getattr(handler, MIO_FILE_HANDLER_PATH_ATTR)
            if hasattr(handler, MIO_FILE_HANDLER_PATH_ATTR)
            else handler.baseFilename
        )
        if handler_path and os.path.abspath(os.fspath(handler_path)) == normalized_log_path:
            return handler
    return None


def _file_handler_uses_utf8(handler: logging.FileHandler) -> bool:
    encoding = handler.encoding
    if encoding is None and handler.stream is not None:
        encoding = handler.stream.encoding
    if encoding is None:
        return False
    return encoding.lower().replace('-', '').replace('_', '') == 'utf8'


def _configure_log_handler(handler: logging.Handler) -> None:
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))


def _configure_mio_file_handler(handler: logging.Handler, normalized_log_path: str) -> None:
    _configure_log_handler(handler)
    setattr(handler, MIO_FILE_HANDLER_ATTR, True)
    setattr(handler, MIO_FILE_HANDLER_PATH_ATTR, normalized_log_path)


def _install_development_console_logging(root_logger: logging.Logger) -> None:
    stream_handler = logging.StreamHandler()
    _configure_log_handler(stream_handler)
    root_logger.addHandler(stream_handler)


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
