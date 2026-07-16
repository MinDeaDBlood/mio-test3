from __future__ import annotations

import json
import platform
from typing import Any, Protocol

from .models import ReleaseAssetSelection, ReleaseCheckResult

DEFAULT_UPDATE_URL = 'https://api.github.com/repos/ColdWindScholar/MIO-KITCHEN-SOURCE/releases/latest'
SUPPORTED_BINARY_MACHINES = frozenset({'AMD64', 'X86_64', 'x86_64'})


class _RequestsLike(Protocol):
    def get(self, url: str): ...


class UpdateFetchError(RuntimeError):
    def __init__(self, message: str, *, raw_text: str = ''):
        super().__init__(message)
        self.raw_text = raw_text


def fetch_release_check(
    update_url: str,
    *,
    current_version: str,
    requests_module: _RequestsLike | None = None,
) -> ReleaseCheckResult:
    """Fetch and normalize latest-release metadata without touching UI state.

    The app layer supplies the current version. This logic layer parses release
    metadata and decides whether a newer package
    exists. ``requests`` stays lazy so importing update UI never imports network
    dependencies at startup.
    """
    if requests_module is None:
        import requests as requests_module  # type: ignore[no-redef]

    response = requests_module.get(update_url)
    raw_text = response.text
    payload = json.loads(raw_text)
    new_version = payload.get('name')
    if new_version is None:
        raise UpdateFetchError('Release response does not contain a version name', raw_text=raw_text)
    return ReleaseCheckResult(
        has_update=not str(new_version).endswith(current_version),
        new_version=str(new_version),
        body=payload.get('body') or '',
        assets=payload.get('assets') or [],
        raw_text=raw_text,
    )


def build_release_package_name(
    package_head: str,
    *,
    system_name: str | None = None,
    machine_name: str | None = None,
) -> str:
    """Return the expected release asset name for the current platform."""
    system_name = system_name or platform.system()
    machine_name = machine_name or platform.machine()
    if system_name == 'Windows':
        return package_head + '-win.zip'
    if system_name == 'Linux':
        return package_head + '-linux.zip'
    if system_name == 'Darwin':
        return package_head + ('-macos-intel.zip' if machine_name == 'x86_64' else '-macos.zip')
    return package_head


def select_release_asset(
    package_head: str,
    assets: list[dict[str, Any]] | None,
    *,
    system_name: str | None = None,
    machine_name: str | None = None,
) -> ReleaseAssetSelection:
    """Select the downloadable asset while preserving existing platform rules."""
    machine_name = machine_name or platform.machine()
    package_name = build_release_package_name(
        package_head,
        system_name=system_name,
        machine_name=machine_name,
    )
    if machine_name not in SUPPORTED_BINARY_MACHINES:
        return ReleaseAssetSelection(package_name=package_name)
    for asset in assets or []:
        if asset.get('name') != package_name:
            continue
        return ReleaseAssetSelection(
            package_name=package_name,
            download_url=asset.get('browser_download_url') or '',
            size=asset.get('size') or 0,
            download_count=asset.get('download_count') or '0',
        )
    return ReleaseAssetSelection(package_name=package_name)
