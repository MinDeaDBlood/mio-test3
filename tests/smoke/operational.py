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
from time import monotonic

import requests

from tests.support.runtime_smoke import (
    LocalCatalogServiceFactory,
    build_store_runtime,
    lang,
    prepare_root,
    sample_store_items,
)
from src.logic.network_downloads import download_api
from src.app.composition.plugin_store import build_plugin_store_composition
from src.ui.tabs.plugins.store.window import MpkStore


def main() -> None:
    root = prepare_root()
    try:
        items = sample_store_items()
        runtime = build_store_runtime(
            root,
            repo_url='https://example.invalid/plugins/',
        )
        factory = LocalCatalogServiceFactory(items)
        window = MpkStore(texts=lang)
        window.withdraw()
        composition = build_plugin_store_composition(
            window,
            runtime=runtime,
            logger=logging,
            requests_loader=lambda: requests,
            download_api_func=download_api,
            store_service_factory=factory,
        )
        window.attach(composition)
        window.open()
        deadline = monotonic() + 5.0
        while window.store_state.catalog_items() != items:
            assert monotonic() < deadline, 'Plugin Store UI refresh timed out.'
            root.update()

        assert composition.repository.repo == runtime.settings.plugin_repo
        assert factory.created == [runtime.settings.plugin_repo]
        assert composition.repository.repository_items() == items
        assert window.store_state.catalog_items() == items
        assert window.store_state.visible_plugin_ids() == ('demo.plugin',)
        controls = window.store_state.controls_for('demo.plugin')
        assert controls and all(control.winfo_exists() for control in controls)
        assert runtime.presence.focus_existing() is True

        composition.repository.persist_repo('https://example.invalid/new/')
        window.request_db_refresh(True)
        deadline = monotonic() + 5.0
        while (
            factory.created[-1] != 'https://example.invalid/new/'
            or window.store_state.catalog_items() != items
        ):
            assert monotonic() < deadline, 'Plugin Store UI refresh timed out.'
            root.update()
        root.update()
        assert runtime.settings.plugin_repo == 'https://example.invalid/new/'
        assert composition.repository.repo == 'https://example.invalid/new/'
        assert composition.repository.repository_items() == items
        assert window.store_state.catalog_items() == items
        assert factory.created[-1] == 'https://example.invalid/new/'

        window._on_close_window()
        assert runtime.presence.focus_existing() is False
    finally:
        root.destroy()

    print('OPERATIONAL_SMOKE_OK')


if __name__ == '__main__':
    main()
