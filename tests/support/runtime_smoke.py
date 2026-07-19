from __future__ import annotations

# Direct file execution bootstrap
import sys as _direct_sys
from pathlib import Path as _DirectPath

_DIRECT_PROJECT_ROOT = _DirectPath(__file__).resolve().parent
while _DIRECT_PROJECT_ROOT != _DIRECT_PROJECT_ROOT.parent:
    if (
        (_DIRECT_PROJECT_ROOT / "src").is_dir()
        and (_DIRECT_PROJECT_ROOT / "tests").is_dir()
        and (_DIRECT_PROJECT_ROOT / "scripts").is_dir()
    ):
        break
    _DIRECT_PROJECT_ROOT = _DIRECT_PROJECT_ROOT.parent
else:
    raise RuntimeError(f"Project root was not found for {__file__}")

_direct_root_text = str(_DIRECT_PROJECT_ROOT)
if _direct_root_text not in _direct_sys.path:
    _direct_sys.path.insert(0, _direct_root_text)
if __package__ in {None, ""}:
    _direct_relative = _DirectPath(__file__).resolve().relative_to(
        _DIRECT_PROJECT_ROOT
    ).with_suffix("")
    __package__ = ".".join(_direct_relative.parts[:-1])


import tempfile
from collections.abc import Iterable, Mapping
from pathlib import Path

from src.app.composition.main_window import compose_main_window, create_main_window
from src.app.composition.window_runtime import initialize_window_runtime
from src.app.localization import load_language_from_files
from src.app.localization_runtime import lang
from src.app.plugins.store.presence import PluginStorePresenceRegistry
from src.app.plugins.store.runtime import PluginStoreRuntimeContext
from src.app.runtime.flags import States
from src.app.runtime.session import ensure_runtime_session, sync_runtime_globals
from src.app.ui_feedback import build_ui_dispatcher
from src.app.ui_tasks import build_ui_task_runner
from src.logic.plugins.models import ModuleErrorCodes
from src.logic.plugins.module_manager import ModuleManager
from src.logic.plugins.store_models import PluginCatalogItem
from src.logic.plugins.store_service import PluginStoreFetchResult
from src.platform.plugin_gateway import PluginGateway
from src.platform.settings_repository import SettingsRepository
from src.ui.tabs.settings.appearance.actions import apply_initial_appearance
from src.ui.main_window import Tool


def prepare_root() -> Tool:
    ensure_runtime_session()
    load_language_from_files('English')
    root = create_main_window()
    root.withdraw()
    runtime = initialize_window_runtime(root)
    apply_initial_appearance(
        window=root,
        theme_var=runtime.theme,
        language_var=runtime.language,
        theme_id='dark',
        language_name='English',
        transparent_enabled=False,
        effect_alpha=1.0,
    )
    compose_main_window(root)
    root.update_idletasks()
    return root


class LocalCatalogService:
    """Deterministic repository boundary for UI-only smoke scenarios.

    The service and MPK network path are covered separately with a real local
    HTTP server in the Plugin Store contract suite.
    """

    def __init__(
        self,
        items: Iterable[PluginCatalogItem | Mapping[str, object]],
    ) -> None:
        self.items = tuple(
            item
            if isinstance(item, PluginCatalogItem)
            else PluginCatalogItem.from_mapping(item, item_index=index)
            for index, item in enumerate(items)
        )
        self.calls: list[bool] = []

    def fetch(self, *, refresh: bool = False) -> PluginStoreFetchResult:
        self.calls.append(bool(refresh))
        return PluginStoreFetchResult(items=self.items)


class LocalCatalogServiceFactory:
    def __init__(
        self,
        items: Iterable[PluginCatalogItem | Mapping[str, object]],
    ) -> None:
        self.items = tuple(items)
        self.created: list[str] = []
        self.services: list[LocalCatalogService] = []

    def __call__(
        self,
        *,
        repo_url,
        local_db_path,
        json_edit_cls,
        requests_module,
        logger,
    ):
        assert local_db_path
        assert json_edit_cls
        assert requests_module
        assert logger
        self.created.append(repo_url)
        service = LocalCatalogService(self.items)
        self.services.append(service)
        return service


def build_store_runtime(root, *, repo_url: str) -> PluginStoreRuntimeContext:
    temp_root = Path(tempfile.mkdtemp(prefix='mio-smoke-store-'))
    workspace = temp_root / 'workspace'
    workspace.mkdir()
    settings_path = temp_root / 'settings.ini'
    settings_path.write_text(
        '[setting]\n'
        f'plugin_repo = {repo_url}\n'
        f'path = {workspace}\n',
        encoding='utf-8',
    )
    settings = SettingsRepository(set_ini=str(settings_path), load=True)
    states = States()
    gateway = PluginGateway(ModuleManager(module_dir=temp_root / 'installed'))
    dispatcher = build_ui_dispatcher(host_window=root)
    return PluginStoreRuntimeContext(
        host_window=root,
        settings=settings,
        plugin_gateway=gateway,
        module_error_codes=ModuleErrorCodes,
        presence=PluginStorePresenceRegistry(states),
        temp_path=str(temp_root / 'downloads'),
        dispatcher=dispatcher,
        task_runner=build_ui_task_runner(
            dispatcher=dispatcher,
            is_alive=lambda: bool(root.winfo_exists()),
        ),
    )


def sample_store_items() -> tuple[PluginCatalogItem, ...]:
    return (
        PluginCatalogItem.from_mapping(
            {
                'id': 'demo.plugin',
                'name': 'Demo Plugin',
                'author': 'MIO',
                'version': '1.0',
                'size': 128,
                'desc': 'Runtime smoke plugin',
                'files': ['demo.mpk'],
                'depend': [],
            }
        ),
    )


__all__ = [
    'LocalCatalogServiceFactory',
    'build_store_runtime',
    'lang',
    'prepare_root',
    'sample_store_items',
    'sync_runtime_globals',
]


if __name__ == "__main__":
    from tests.support.direct_execution import support_module_main

    raise SystemExit(support_module_main(__file__))
