"""Periodic stack dumps for startup hangs."""
from __future__ import annotations

import faulthandler
import logging
from typing import TextIO

_ACTIVE = False


def start_watchdog(stream: TextIO | None, timeout_seconds: int) -> bool:
    global _ACTIVE
    if stream is None:
        return False
    try:
        if _ACTIVE:
            faulthandler.cancel_dump_traceback_later()
        faulthandler.dump_traceback_later(
            timeout_seconds,
            repeat=True,
            file=stream,
        )
    except (RuntimeError, ValueError, OSError):
        logging.getLogger('mio.startup').exception(
            'Unable to start the startup watchdog'
        )
        return False
    _ACTIVE = True
    logging.getLogger('mio.startup').info(
        'Startup watchdog armed: timeout=%ss repeat=true',
        timeout_seconds,
    )
    return True


def stop_watchdog() -> bool:
    global _ACTIVE
    if not _ACTIVE:
        return False
    try:
        faulthandler.cancel_dump_traceback_later()
    except RuntimeError:
        pass
    _ACTIVE = False
    logging.getLogger('mio.startup').info('Startup watchdog disarmed')
    return True


__all__ = ['start_watchdog', 'stop_watchdog']
