from __future__ import annotations

from src.app.runtime.session import ensure_runtime_session, sync_runtime_globals


def init(args):
    """Public startup entry point with explicit runtime session preparation."""
    ensure_runtime_session()
    from src.app.bootstrap import init as _bootstrap_init
    return _bootstrap_init(args)


def restart(er=None):
    """Restart the tool using the already-initialized runtime session."""
    ensure_runtime_session()
    from src.app.bootstrap import restart as _bootstrap_restart
    return _bootstrap_restart(er)


__all__ = ['init', 'restart', 'sync_runtime_globals']
