from __future__ import annotations

import logging
import os
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Protocol


from requests import RequestException

from src.logic.plugins.store_models import PluginCatalogItemProtocol


class StorePluginInstallPort(Protocol):
    def is_installed(self, plugin_id: str) -> bool: ...
    def install(self, package_path: str) -> tuple[object, str]: ...


class StoreModuleErrorCodesProtocol(Protocol):
    Normal: object


DownloadProgress = tuple[object, object, object, object, object]


class DownloadApi(Protocol):
    def __call__(
        self,
        url: str,
        path: str,
        int_: bool = True,
        size_: int = 0,
        chunk_size: int = 2048576,
    ) -> Iterable[DownloadProgress]: ...


ProgressCallback = Callable[[int], None]


@dataclass(frozen=True, slots=True)
class StoreInstallResult:
    ok: bool
    plugin_id: str
    error_kind: str = ""
    error_reason: str = ""
    failing_dependency_id: str = ""
    completed_files: tuple[str, ...] = field(default_factory=tuple)


class StorePluginInstallService:
    """Dependency aware repository install lifecycle without Tk dependencies."""

    def __init__(
        self,
        *,
        repo_url: str,
        temp_path: str,
        plugin_install_port: StorePluginInstallPort,
        module_error_codes: StoreModuleErrorCodesProtocol,
        download_api_func: DownloadApi,
        logger: logging.Logger | None = None,
    ) -> None:
        self.repo_url = repo_url
        self.temp_path = temp_path
        self.plugin_install_port = plugin_install_port
        self.module_error_codes = module_error_codes
        self.download_api_func = download_api_func
        self.logger = logger or logging.getLogger(__name__)

    def install_from_repo(
        self,
        *,
        plugin_id: str,
        files: tuple[str, ...],
        size: int,
        depends: tuple[str, ...],
        repository_items: tuple[PluginCatalogItemProtocol, ...],
        progress_callback: ProgressCallback | None = None,
        is_alive: Callable[[], bool] | None = None,
        active_stack: set[str] | None = None,
    ) -> StoreInstallResult:
        is_alive = is_alive or (lambda: True)
        active_stack = set(active_stack or ())
        if plugin_id in active_stack:
            return StoreInstallResult(
                False, plugin_id, error_kind="dependency-cycle", error_reason=plugin_id
            )
        active_stack.add(plugin_id)

        repo_by_id = {item.plugin_id: item for item in repository_items}

        for dependency_id in depends:
            if not dependency_id or self.plugin_install_port.is_installed(dependency_id):
                continue
            dependency = repo_by_id.get(dependency_id)
            if dependency is None:
                return StoreInstallResult(
                    False,
                    plugin_id,
                    error_kind="dependency-not-found",
                    failing_dependency_id=dependency_id,
                )
            dependency_result = self.install_from_repo(
                plugin_id=dependency.plugin_id,
                files=dependency.files,
                size=dependency.size_bytes,
                depends=dependency.dependencies,
                repository_items=repository_items,
                progress_callback=progress_callback,
                is_alive=is_alive,
                active_stack=active_stack,
            )
            if not dependency_result.ok:
                return StoreInstallResult(
                    False,
                    plugin_id,
                    error_kind="dependency-install-failed",
                    error_reason=dependency_result.error_reason,
                    failing_dependency_id=dependency_id,
                )
            if not self.plugin_install_port.is_installed(dependency_id):
                return StoreInstallResult(
                    False,
                    plugin_id,
                    error_kind="dependency-install-failed",
                    failing_dependency_id=dependency_id,
                )

        if not files:
            return StoreInstallResult(False, plugin_id, error_kind="no-files")

        completed_files: list[str] = []
        try:
            for file_name in files:
                if not is_alive():
                    return StoreInstallResult(
                        False,
                        plugin_id,
                        error_kind="cancelled",
                        completed_files=tuple(completed_files),
                    )
                local_path = os.path.join(self.temp_path, file_name)
                expected_size = size
                if not (
                    os.path.exists(local_path)
                    and os.path.isfile(local_path)
                    and (
                        expected_size <= 0
                        or os.path.getsize(local_path) == expected_size
                    )
                ):
                    generator = self.download_api_func(
                        self.repo_url + file_name,
                        self.temp_path,
                        size_=expected_size,
                        chunk_size=max(262144, ((expected_size or 0) // 4) or 0),
                    )
                    for (
                        percentage,
                        _speed,
                        _downloaded,
                        _file_size,
                        _elapsed,
                    ) in generator:
                        if not is_alive():
                            return StoreInstallResult(
                                False,
                                plugin_id,
                                error_kind="cancelled",
                                completed_files=tuple(completed_files),
                            )
                        if percentage == "Error":
                            return StoreInstallResult(
                                False,
                                plugin_id,
                                error_kind="download-error",
                                error_reason=file_name,
                                completed_files=tuple(completed_files),
                            )
                        if progress_callback is not None:
                            if isinstance(percentage, (int, float, str)):
                                progress_callback(int(percentage))
                            else:
                                raise TypeError(
                                    "Download progress must be numeric or a numeric string."
                                )
                install_result, reason_text = self.plugin_install_port.install(local_path)
                if install_result != self.module_error_codes.Normal:
                    return StoreInstallResult(
                        False,
                        plugin_id,
                        error_kind="install-error",
                        error_reason=str(reason_text),
                        completed_files=tuple(completed_files),
                    )
                completed_files.append(file_name)
        except RequestException as exc:
            self.logger.exception(
                "StorePluginInstallService.install_from_repo network error for %s: %s",
                plugin_id,
                exc,
            )
            return StoreInstallResult(
                False,
                plugin_id,
                error_kind="network-error",
                error_reason=str(exc),
                completed_files=tuple(completed_files),
            )
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            self.logger.exception(
                "StorePluginInstallService.install_from_repo operation error for %s: %s",
                plugin_id,
                exc,
            )
            return StoreInstallResult(
                False,
                plugin_id,
                error_kind="unexpected-error",
                error_reason=str(exc),
                completed_files=tuple(completed_files),
            )
        return StoreInstallResult(
            True, plugin_id, completed_files=tuple(completed_files)
        )
