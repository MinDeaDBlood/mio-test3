from __future__ import annotations

import logging
from collections.abc import Callable

from src.app.plugins.store.host_port import PluginStoreHostPort
from src.logic.plugins.store_install import (
    StoreInstallResult,
    StorePluginInstallService,
)


class PluginStoreInstallController:
    """Run repository installation and report state through explicit callbacks."""

    def __init__(
        self,
        *,
        service_builder: Callable[[], StorePluginInstallService],
        host_port: PluginStoreHostPort,
        logger: logging.Logger | None = None,
    ) -> None:
        self.host_port = host_port
        self.service_builder = service_builder
        self.logger = logger or logging.getLogger(__name__)

    def start(
        self,
        files: tuple[str, ...],
        size: int,
        plugin_id: str,
        dependencies: tuple[str, ...],
        *,
        on_started: Callable[[str], None],
        on_progress: Callable[[str, int], None],
        on_finished: Callable[[str, str, StoreInstallResult], None],
    ) -> bool:
        state = self.host_port.state
        if not self.host_port.is_alive():
            return False
        if not state.start_task(plugin_id):
            self.logger.info(
                "PluginStoreInstallController.start: %s already in progress",
                plugin_id,
            )
            return False

        plugin_info = self.host_port.repository.plugin_info_for(plugin_id)
        display_name = plugin_info.name if plugin_info is not None else plugin_id
        on_started(plugin_id)

        def worker() -> StoreInstallResult:
            service = self.service_builder()
            return service.install_from_repo(
                plugin_id=plugin_id,
                files=files,
                size=size,
                depends=dependencies,
                repository_items=self.host_port.repository.repository_items(),
                progress_callback=lambda percentage: self.host_port.dispatcher.dispatch(
                    on_progress,
                    plugin_id,
                    percentage,
                ),
                is_alive=self.host_port.is_alive,
            )

        def finish(result: StoreInstallResult) -> None:
            try:
                on_finished(plugin_id, display_name, result)
            finally:
                self.host_port.update_plugin_state(plugin_id)

        def success(result: StoreInstallResult) -> None:
            state.finish_task(plugin_id)
            finish(result)

        def failure(exc: Exception) -> None:
            self.logger.exception(
                "Plugin Store install failed for %s",
                plugin_id,
            )
            state.finish_task(plugin_id)
            finish(
                StoreInstallResult(
                    False,
                    plugin_id,
                    error_kind="unexpected-error",
                    error_reason=str(exc),
                )
            )

        self.host_port.task_runner.run(
            worker,
            on_success=success,
            on_error=failure,
        )
        return True


__all__ = ["PluginStoreInstallController"]
