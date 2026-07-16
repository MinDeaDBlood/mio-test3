from __future__ import annotations

import logging

_CASE_SENSITIVE_UNSUPPORTED_WINERRORS = {50, 145}


def is_case_sensitive_unsupported_error(exc: OSError) -> bool:
    if not hasattr(exc, 'winerror'):
        return False
    return exc.winerror in _CASE_SENSITIVE_UNSUPPORTED_WINERRORS


def log_case_sensitive_enable_failure(exc: OSError, work_path: str) -> None:
    if is_case_sensitive_unsupported_error(exc):
        logging.warning(
            'unpack.workflow.enable_case_sensitive_unsupported: work_path=%s winerror=%s reason=%s',
            work_path,
            exc.winerror,
            exc,
        )
        return
    logging.exception('unpack.workflow.enable_case_sensitive_failed: work_path=%s', work_path)


__all__ = ['is_case_sensitive_unsupported_error', 'log_case_sensitive_enable_failure']
