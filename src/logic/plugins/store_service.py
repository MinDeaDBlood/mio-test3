from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol


from src.logic.plugins.store_models import (
    PluginCatalogItem,
    PluginCatalogValidationError,
    parse_plugin_catalog,
)


class JsonStoreProtocol(Protocol):
    def read(self) -> object: ...
    def write(self, value: object) -> object: ...


class HttpResponseProtocol(Protocol):
    def raise_for_status(self) -> None: ...
    def json(self) -> object: ...


class RequestsExceptionsProtocol(Protocol):
    RequestException: type[Exception]


class RequestsModuleProtocol(Protocol):
    exceptions: RequestsExceptionsProtocol

    def get(self, url: str, *, timeout: int) -> HttpResponseProtocol: ...


@dataclass(frozen=True, slots=True)
class PluginStoreFetchResult:
    items: tuple[PluginCatalogItem, ...]
    error_text: str = ''
    error_title: str = 'Repository Error'

    @property
    def ok(self) -> bool:
        return not self.error_text


class PluginStoreService:
    def __init__(
        self,
        *,
        repo_url: str,
        local_db_path: str,
        json_edit_cls: Callable[[str], JsonStoreProtocol],
        requests_module: RequestsModuleProtocol,
        logger: logging.Logger | None = None,
    ) -> None:
        self.repo_url = repo_url
        self.local_db_path = local_db_path
        self.json_edit_cls = json_edit_cls
        self.requests_module = requests_module
        self.logger = logger or logging.getLogger(__name__)

    def fetch(self, *, refresh: bool = False) -> PluginStoreFetchResult:
        try:
            if not refresh:
                local_items = self._read_local_database()
                if local_items:
                    return PluginStoreFetchResult(items=local_items)
            items = self._fetch_remote()
            self._write_local_database(items)
            return PluginStoreFetchResult(items=items)
        except self.requests_module.exceptions.RequestException as exc:
            self.logger.error('PluginStoreService.fetch network error: %s', exc)
            return PluginStoreFetchResult(
                items=(),
                error_text=str(exc),
                error_title='Repository Error',
            )
        except (json.JSONDecodeError, PluginCatalogValidationError) as exc:
            self.logger.error('PluginStoreService.fetch parse error: %s', exc)
            return PluginStoreFetchResult(
                items=(),
                error_text='Error parsing plugin list.',
                error_title='Repository Error',
            )
        except (OSError, TypeError, ValueError) as exc:
            self.logger.exception('PluginStoreService.fetch storage or validation error: %s', exc)
            return PluginStoreFetchResult(
                items=(),
                error_text=str(exc),
                error_title='Repository Error',
            )

    def _read_local_database(self) -> tuple[PluginCatalogItem, ...]:
        payload = self.json_edit_cls(self.local_db_path).read()
        if payload in (None, []):
            return ()
        return parse_plugin_catalog(payload)

    def _write_local_database(self, items: tuple[PluginCatalogItem, ...]) -> None:
        payload = [item.to_mapping() for item in items]
        self.json_edit_cls(self.local_db_path).write(payload)

    def _fetch_remote(self) -> tuple[PluginCatalogItem, ...]:
        response = self.requests_module.get(self.repo_url + 'plugin.json', timeout=10)
        response.raise_for_status()
        return parse_plugin_catalog(response.json())


__all__ = [
    'HttpResponseProtocol',
    'JsonStoreProtocol',
    'PluginStoreFetchResult',
    'PluginStoreService',
    'RequestsModuleProtocol',
]
