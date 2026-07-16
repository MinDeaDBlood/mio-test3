from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from src.platform.runtime_paths import POSTINSTALL_TEMPLATE_FILE
from src.logic.projects.pack.postinstall import (
    PostInstallConfigRepository,
    PostInstallEntry,
    validate_partition_name,
)


class PostInstallConfigController:
    """Application boundary for loading and saving postinstall configuration."""

    def __init__(self, repository: PostInstallConfigRepository) -> None:
        self._repository = repository

    def load(self) -> dict[str, PostInstallEntry]:
        return self._repository.load()

    def normalize_partition_name(self, partition: str) -> str:
        return validate_partition_name(partition)

    def create_entry(
        self,
        partition: str,
        *,
        run_postinstall: bool = False,
        postinstall_path: str = "",
        filesystem_type: str = "",
        postinstall_optional: bool = False,
    ) -> PostInstallEntry:
        return PostInstallEntry(
            partition=self.normalize_partition_name(partition),
            run_postinstall=bool(run_postinstall),
            postinstall_path=str(postinstall_path),
            filesystem_type=str(filesystem_type),
            postinstall_optional=bool(postinstall_optional),
        )

    def save(self, entries: Iterable[PostInstallEntry]) -> None:
        self._repository.save(entries)


def build_postinstall_config_controller(
    config_file: str | Path | None = None,
) -> PostInstallConfigController:
    path = Path(config_file) if config_file is not None else POSTINSTALL_TEMPLATE_FILE
    return PostInstallConfigController(PostInstallConfigRepository(path))


__all__ = ["PostInstallConfigController", "build_postinstall_config_controller"]
