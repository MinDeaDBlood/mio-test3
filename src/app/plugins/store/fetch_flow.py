"""Fetch lifecycle controller for the Plugin Store window."""

from __future__ import annotations

from collections.abc import Callable


import logging

from src.app.plugins.store.host_port import PluginStoreHostPort
from src.logic.plugins.store_service import PluginStoreFetchResult


class PluginStoreFetchController:
    def __init__(
        self,
        *,
        apply_fetch_result: Callable[[PluginStoreFetchResult], bool],
        host_port: PluginStoreHostPort,
        logger: logging.Logger | None = None,
    ) -> None:
        self.host_port = host_port
        self._apply_fetch_result = apply_fetch_result
        self.logger = logger or logging.getLogger(__name__)

    def apply_result(self, result: PluginStoreFetchResult) -> bool:
        self.host_port.state.finish_fetch()
        return self._apply_fetch_result(result)

    def handle_error(self, exc: Exception) -> bool:
        self.logger.error(
            "MpkStore.request_db_refresh worker failed",
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        return self.apply_result(
            PluginStoreFetchResult(
                items=(),
                error_text=str(exc),
                error_title="",
            )
        )

    def fetch_db(self, refresh: bool = False) -> PluginStoreFetchResult:
        return self.host_port.repository.fetch(refresh=refresh)

    def _initialize_and_fetch(
        self,
        initialize: Callable[[], object],
        refresh: bool,
    ) -> PluginStoreFetchResult:
        initialize()
        return self.fetch_db(refresh)

    def _request_worker(self, worker: Callable[..., PluginStoreFetchResult], *args: object) -> bool:
        view_state = self.host_port.state
        if not view_state.start_fetch():
            self.logger.debug("MpkStore.request_db_refresh: fetch already in progress.")
            return False
        try:
            self.host_port.task_runner.run(
                worker,
                *args,
                on_success=self.apply_result,
                on_error=self.handle_error,
            )
            return True
        except (RuntimeError, TypeError, ValueError) as exc:
            self.handle_error(exc)
            return False

    def request_initial_refresh(self, initialize: Callable[[], object]) -> bool:
        """Initialize the network repository and fetch outside the Tk thread."""
        return self._request_worker(self._initialize_and_fetch, initialize, False)

    def request_refresh(self, refresh: bool = False) -> bool:
        return self._request_worker(self.fetch_db, refresh)


__all__ = ["PluginStoreFetchController"]
