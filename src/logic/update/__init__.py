from __future__ import annotations

__all__ = [
    'DEFAULT_UPDATE_URL',
    'SUPPORTED_BINARY_MACHINES',
    'ReleaseAssetSelection',
    'ReleaseCheckResult',
    'PreparedUpdatePayload',
    'UpdateApplyResult',
    'UpdateCleanupResult',
    'UpdateFetchError',
    'apply_staged_update',
    'build_release_package_name',
    'build_tool_binary_name',
    'build_updater_path',
    'cleanup_completed_update',
    'fetch_release_check',
    'prepare_update_payload',
    'select_release_asset',
]

_lazy_exports = {
    'DEFAULT_UPDATE_URL': '.service',
    'SUPPORTED_BINARY_MACHINES': '.service',
    'UpdateFetchError': '.service',
    'build_release_package_name': '.service',
    'fetch_release_check': '.service',
    'select_release_asset': '.service',
    'apply_staged_update': '.install_service',
    'build_tool_binary_name': '.install_service',
    'build_updater_path': '.install_service',
    'cleanup_completed_update': '.install_service',
    'prepare_update_payload': '.install_service',
    'ReleaseAssetSelection': '.models',
    'ReleaseCheckResult': '.models',
    'PreparedUpdatePayload': '.models',
    'UpdateApplyResult': '.models',
    'UpdateCleanupResult': '.models',
}


def __getattr__(name: str):
    if name not in _lazy_exports:
        raise AttributeError(name)
    from importlib import import_module

    module = import_module(_lazy_exports[name], __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
