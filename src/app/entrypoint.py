from __future__ import annotations

import logging

from src.app.runtime.session import ensure_runtime_session, sync_runtime_globals
from src.platform.crash_logging import log_startup_phase, operation_context

logger = logging.getLogger(__name__)


def init(args):
    """Public startup entry point with explicit runtime session preparation."""
    with operation_context('startup.runtime_session'):
        ensure_runtime_session()
    log_startup_phase('runtime session ready')
    with operation_context('startup.bootstrap'):
        from src.app.bootstrap import init as _bootstrap_init

        return _bootstrap_init(args)


def restart(er=None):
    """Restart the tool using the already initialized runtime session."""
    logger.info('Application restart requested: %r', er)
    ensure_runtime_session()
    from src.app.bootstrap import restart as _bootstrap_restart

    return _bootstrap_restart(er)


__all__ = ['init', 'restart', 'sync_runtime_globals']
