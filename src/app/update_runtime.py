from __future__ import annotations

from src.app.runtime.contexts.settings import resolve_settings
from src.logic.update.models import ReleaseCheckResult
from src.logic.update.service import DEFAULT_UPDATE_URL, fetch_release_check


def resolve_update_url() -> str:
    return resolve_settings().update_url or DEFAULT_UPDATE_URL


def fetch_current_release_check(update_url: str) -> ReleaseCheckResult:
    return fetch_release_check(
        update_url,
        current_version=resolve_settings().version,
    )


__all__ = ['fetch_current_release_check', 'resolve_update_url']
