from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReleaseCheckResult:
    has_update: bool
    new_version: str | None = None
    body: str = ''
    assets: list[dict[str, Any]] | None = None
    raw_text: str = ''


@dataclass(frozen=True)
class PreparedUpdatePayload:
    update_dict: dict[str, str]
    updater_path: str


@dataclass(frozen=True)
class ReleaseAssetSelection:
    package_name: str
    download_url: str = ''
    size: int = 0
    download_count: int | str = '0'

    @property
    def found(self) -> bool:
        return bool(self.download_url)

@dataclass(frozen=True)
class UpdateApplyResult:
    success: bool
    settings_updates: dict[str, str]
    launch_path: str = ''
    warning_paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class UpdateCleanupResult:
    removed_paths: tuple[str, ...]
    failed_paths: tuple[str, ...]

