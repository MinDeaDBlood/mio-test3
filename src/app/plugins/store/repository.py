from __future__ import annotations

import logging
from collections.abc import Callable

from src.core.json_store import JsonEdit
from src.app.runtime.contexts.contracts import (
    ModuleErrorCodesProtocol,
    PluginGatewayProtocol,
    SettingsProtocol,
)
from src.logic.plugins.store_install.service import (
    DownloadApi,
    StorePluginInstallService,
)
from src.logic.plugins.store_models import PluginCatalogItem
from src.logic.plugins.store_service import (
    PluginStoreFetchResult,
    PluginStoreService,
    RequestsModuleProtocol,
)

DEFAULT_PLUGIN_REPOSITORY = (
    "https://raw.githubusercontent.com/ColdWindScholar/MPK_Plugins/main/"
)


StoreServiceFactory = Callable[..., PluginStoreService]
RequestsLoader = Callable[[], RequestsModuleProtocol]


class PluginStoreRepositorySession:
    """Repository selection and service composition for the Plugin Store."""

    def __init__(
        self,
        *,
        settings: SettingsProtocol,
        temp_path: str,
        local_db_path: str,
        plugin_gateway: PluginGatewayProtocol,
        module_error_codes: ModuleErrorCodesProtocol,
        requests_loader: RequestsLoader,
        download_api_func: DownloadApi,
        store_service_factory: StoreServiceFactory = PluginStoreService,
        logger: logging.Logger | None = None,
    ) -> None:
        self.settings = settings
        self.temp_path = temp_path
        self.local_db_path = local_db_path
        self.plugin_gateway = plugin_gateway
        self.module_error_codes = module_error_codes
        self.requests_loader = requests_loader
        self.download_api_func = download_api_func
        self.store_service_factory = store_service_factory
        self.logger = logger or logging.getLogger(__name__)
        self.repo = ""
        self.store_service: PluginStoreService | None = None
        self._catalog_items: tuple[PluginCatalogItem, ...] = ()

    def current_configured_repo(self) -> str:
        return self.settings.plugin_repo or self.repo

    def init_from_settings(self) -> str:
        configured_repo = self.settings.plugin_repo
        self.set_repo(configured_repo or DEFAULT_PLUGIN_REPOSITORY)
        self.logger.info("MpkStore: Repository initialized to: %s", self.repo)
        return self.repo

    def set_repo(self, repo: str) -> None:
        normalized = repo.strip()
        if not normalized:
            raise ValueError("Plugin repository URL is empty")
        self.repo = normalized
        self.store_service = self._create_store_service()

    def persist_repo(self, repo: str) -> None:
        self.settings.set_value("plugin_repo", repo)
        self.set_repo(repo)

    def _create_store_service(self) -> PluginStoreService:
        return self.store_service_factory(
            repo_url=self.repo,
            local_db_path=self.local_db_path,
            json_edit_cls=JsonEdit,
            requests_module=self.requests_loader(),
            logger=self.logger,
        )

    def build_fetch_service(self) -> PluginStoreService:
        if self.store_service is None:
            raise RuntimeError("Plugin repository session is not initialized")
        return self.store_service

    def refresh_store_service(self) -> PluginStoreService:
        if not self.repo:
            raise RuntimeError("Plugin repository session is not initialized")
        self.store_service = self._create_store_service()
        return self.store_service

    def fetch(self, *, refresh: bool = False) -> PluginStoreFetchResult:
        result = self.build_fetch_service().fetch(refresh=refresh)
        self._catalog_items = result.items
        return result

    def repository_items(self) -> tuple[PluginCatalogItem, ...]:
        return self._catalog_items

    def plugin_info_for(self, plugin_id: str) -> PluginCatalogItem | None:
        return next(
            (item for item in self._catalog_items if item.plugin_id == plugin_id),
            None,
        )

    def build_install_service(self) -> StorePluginInstallService:
        if not self.repo:
            raise RuntimeError("Plugin repository session is not initialized")
        return StorePluginInstallService(
            repo_url=self.repo,
            temp_path=self.temp_path,
            plugin_install_port=self.plugin_gateway,
            module_error_codes=self.module_error_codes,
            download_api_func=self.download_api_func,
            logger=self.logger,
        )


__all__ = [
    "DEFAULT_PLUGIN_REPOSITORY",
    "PluginStoreRepositorySession",
    "RequestsLoader",
    "StoreServiceFactory",
]
