from __future__ import annotations

from dataclasses import dataclass

from src.app.runtime.contract import CORE_RUNTIME_KEYS, validate_runtime_keys
from src.app.runtime.defaults import EarlyRuntimeDefaults, get_early_runtime_defaults, register_runtime_defaults
from src.app.runtime.models import RuntimeBootstrapServices
from src.app.runtime.service_bootstrap import build_runtime_bootstrap_services
from src.app.runtime.sync import sync_core_runtime_services, sync_runtime_globals as _sync_runtime_globals
from src.platform.startup import prepare_startup_platform


@dataclass(frozen=True)
class RuntimeSession:
    runtime_defaults: EarlyRuntimeDefaults
    bootstrap_services: RuntimeBootstrapServices


_SESSION: RuntimeSession | None = None


def ensure_runtime_session() -> RuntimeSession:
    global _SESSION
    if _SESSION is None:
        register_runtime_defaults()
        prepare_startup_platform()
        runtime_defaults = get_early_runtime_defaults()
        bootstrap_services = build_runtime_bootstrap_services()
        sync_core_runtime_services(**bootstrap_services.export_runtime_values())
        validate_runtime_keys(CORE_RUNTIME_KEYS, context='core runtime bootstrap')
        _SESSION = RuntimeSession(
            runtime_defaults=runtime_defaults,
            bootstrap_services=bootstrap_services,
        )
    return _SESSION


def sync_runtime_globals(**kwargs):
    ensure_runtime_session()
    return _sync_runtime_globals(**kwargs)


__all__ = ['RuntimeSession', 'ensure_runtime_session', 'sync_runtime_globals']
