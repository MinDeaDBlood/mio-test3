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


import logging
import tempfile
from pathlib import Path
from time import monotonic

import requests

from tests.support.runtime_smoke import (
    LocalCatalogServiceFactory,
    build_store_runtime,
    lang,
    prepare_root,
    sample_store_items,
    sync_runtime_globals,
)
from src.app.composition.plugin_store import build_plugin_store_composition
from src.app.runtime.phases import require_registered_bootstrap_window_runtime
from src.logic.plugins.events import PluginStateChangedEvent, plugin_event_bus
from src.logic.projects.common.project_manager import ProjectManager
from src.logic.projects.common.runtime_context import build_project_path_runtime_context
from src.logic.network_downloads import download_api
from src.platform.settings_repository import SettingsRepository
from src.ui.tabs.plugins.store.window import MpkStore


def main() -> None:
    root = prepare_root()
    try:
        window_runtime = require_registered_bootstrap_window_runtime()
        with tempfile.TemporaryDirectory(prefix='mio-lifecycle-') as td:
            settings = SettingsRepository(
                set_ini=str(Path(td) / 'settings.ini'),
                load=False,
            )
            settings.path = td
            manager = ProjectManager(
                runtime=build_project_path_runtime_context(
                    workspace_path=settings.path,
                    current_project_name=window_runtime.current_project_name,
                )
            )
            sync_runtime_globals(
                settings=settings,
                project_manager=manager,
                current_project_name=window_runtime.current_project_name,
            )
            window_runtime.current_project_name.set('Lifecycle')
            manager.new('Lifecycle')
            assert manager.current_project_name is window_runtime.current_project_name
            assert manager.exist('Lifecycle')

        items = sample_store_items()
        runtime = build_store_runtime(
            root,
            repo_url='https://example.invalid/plugins/',
        )
        factory = LocalCatalogServiceFactory(items)
        store = MpkStore(texts=lang)
        store.withdraw()
        composition = build_plugin_store_composition(
            store,
            runtime=runtime,
            logger=logging,
            requests_loader=lambda: requests,
            download_api_func=download_api,
            store_service_factory=factory,
        )
        store.attach(composition)
        store.open()
        deadline = monotonic() + 5.0
        while store.store_state.catalog_items() != items:
            assert monotonic() < deadline, 'Plugin Store UI refresh timed out.'
            root.update()
        assert runtime.presence.focus_existing()

        plugin_event_bus.publish(PluginStateChangedEvent(plugin_id='demo.plugin'))
        store.update_idletasks()
        assert store.store_state.controls_for('demo.plugin')

        store._on_close_window()
        plugin_event_bus.publish(PluginStateChangedEvent(plugin_id='demo.plugin'))
        assert not runtime.presence.focus_existing()
    finally:
        root.destroy()

    print('LIFECYCLE_SMOKE_OK')


if __name__ == '__main__':
    main()
