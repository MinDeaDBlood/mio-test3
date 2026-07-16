"""Application coordinator for one Plugin Store window session."""

from __future__ import annotations

from collections.abc import Callable, Sequence
import logging
from typing import TYPE_CHECKING

from src.app.plugins.store.contracts import PluginStoreStateControllerPort

if TYPE_CHECKING:
    from src.app.plugins.store.fetch_flow import PluginStoreFetchController
    from src.app.plugins.store.install_flow import PluginStoreInstallController
    from src.app.plugins.store.repository import PluginStoreRepositorySession
    from src.app.plugins.store.session import PluginStoreWindowSession
    from src.app.plugins.store.uninstall_flow import PluginStoreUninstallController
    from src.app.startup_metrics import FeatureTimeline
    from src.logic.plugins.events import PluginStateChangedEvent
    from src.logic.plugins.store_install import (
        StorePluginInstallService,
    )
    from src.logic.plugins.store_service import (
        PluginStoreFetchResult,
        PluginStoreService,
    )
    from src.logic.plugins.uninstall.result import PluginUninstallResult


class PluginStoreWindowController:
    """Coordinate workflows without importing Tkinter or concrete UI classes."""

    def __init__(
        self,
        *,
        session: PluginStoreWindowSession,
        repository: PluginStoreRepositorySession,
        state_controller: PluginStoreStateControllerPort,
        install_controller: PluginStoreInstallController,
        uninstall_controller: PluginStoreUninstallController,
        fetch_controller: PluginStoreFetchController,
        logger: logging.Logger,
        build_layout: Callable[[], None],
        center_window: Callable[[], None],
        request_repository_url: Callable[[str, Callable[[str], None]], object],
        timeline: FeatureTimeline | None = None,
    ) -> None:
        self.session = session
        self.repository = repository
        self.state_controller = state_controller
        self.install_controller = install_controller
        self.uninstall_controller = uninstall_controller
        self.fetch_controller = fetch_controller
        self.logger = logger
        self._build_layout = build_layout
        self._center_window = center_window
        self._request_repository_url = request_repository_url
        self._timeline = timeline

    def open(self) -> None:
        self.session.open()
        self.session.ensure_background_plugin_load()
        self.init_repo()
        self._build_layout()
        self.request_db_refresh()
        self._center_window()
        if self._timeline is not None:
            self._timeline.log(logger=self.logger)

    def close(self) -> None:
        self.session.close()

    def consume_plugin_events(self, events: Sequence[PluginStateChangedEvent]) -> None:
        self.state_controller.consume_events(events)

    def refresh_visible_plugin_states(self) -> None:
        self.state_controller.refresh_visible_plugin_states()

    def update_plugin_state(self, plugin_id: str) -> bool:
        return self.state_controller.update_plugin_state(plugin_id)

    def apply_uninstall_result(
        self, plugin_id: str, result: PluginUninstallResult
    ) -> None:
        self.state_controller.apply_uninstall_result(plugin_id, result)

    def init_repo(self) -> str:
        return self.repository.init_from_settings()

    def refresh_store_service(self) -> PluginStoreService:
        return self.repository.refresh_store_service()

    def build_store_install_service(self) -> StorePluginInstallService:
        return self.repository.build_install_service()

    def start_download_async(
        self,
        files: tuple[str, ...],
        size: int,
        plugin_id: str,
        dependencies: tuple[str, ...],
    ) -> bool:
        return self.install_controller.start(
            files,
            size,
            plugin_id,
            dependencies,
            on_started=self.state_controller.mark_installing,
            on_progress=self.state_controller.update_install_progress,
            on_finished=self.state_controller.apply_install_result,
        )

    def start_uninstall_async(self, plugin_id: str) -> bool:
        return self.uninstall_controller.start(plugin_id)

    def apply_store_fetch_result(self, result: PluginStoreFetchResult) -> bool:
        return self.fetch_controller.apply_result(result)

    def handle_store_fetch_error(self, exc: Exception) -> bool:
        return self.fetch_controller.handle_error(exc)

    def fetch_db(self, refresh: bool = False) -> PluginStoreFetchResult:
        return self.fetch_controller.fetch_db(refresh)

    def request_db_refresh(self, refresh: bool = False) -> bool:
        return self.fetch_controller.request_refresh(refresh)

    def modify_repo(self) -> object:
        current_value = self.repository.current_configured_repo()

        def accept(new_value: str) -> None:
            if new_value == current_value:
                return
            self.repository.persist_repo(new_value)
            self.request_db_refresh(True)

        return self._request_repository_url(current_value, accept)


__all__ = ["PluginStoreWindowController"]
