"""Apply Plugin Store fetch results to view state and rendered cards."""

from __future__ import annotations

import logging
from collections.abc import Callable

from src.ui.localization import LocalizationCatalog
from src.ui.tabs.plugins.store.contracts import (
    PluginStoreFetchResultProtocol,
    StoreCatalogProtocol,
    StoreNotifierProtocol,
    StoreViewStateProtocol,
)
from src.ui.tabs.plugins.store import keys


class PluginStoreCatalogRefreshController:
    """Replace the validated catalog and update its rendered cards."""

    def __init__(
        self,
        *,
        texts: LocalizationCatalog,
        catalog: StoreCatalogProtocol,
        state: StoreViewStateProtocol,
        notifier: StoreNotifierProtocol,
        is_alive: Callable[[], bool],
        logger: logging.Logger | None = None,
    ) -> None:
        self.texts = texts
        self.catalog = catalog
        self.state = state
        self.notifier = notifier
        self.is_alive = is_alive
        self.logger = logger or logging.getLogger(__name__)

    def apply_fetch_result(self, result: PluginStoreFetchResultProtocol) -> bool:
        if not self.is_alive():
            return False
        self.catalog.clear()
        self.state.replace_catalog(result.items)
        if not result.ok:
            self.logger.warning(
                "Plugin Store catalog was cleared because repository fetch failed."
            )
            message = result.error_text or self.texts.resolve_required_ui_text(
                keys.REPOSITORY_PARSE_ERROR_MESSAGE
            )
            title = result.error_title or self.texts.resolve_required_ui_text(
                keys.REPOSITORY_PARSE_ERROR_DIALOG_TITLE
            )
            self.notifier.show(message, color="orange", title=title)
        self.catalog.add_app(result.items)
        return True


__all__ = ["PluginStoreCatalogRefreshController"]
