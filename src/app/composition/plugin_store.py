"""Composition boundary for the Plugin Store window."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import cast

from src.app.localization_runtime import lang
from src.app.composition import plugin_store_keys as keys
from src.app.plugins.store.fetch_flow import PluginStoreFetchController
from src.app.plugins.store.host_port import (
    PluginStoreHostPort,
    build_plugin_store_host_port,
)
from src.app.plugins.store.install_flow import PluginStoreInstallController
from src.app.plugins.store.repository import (
    PluginStoreRepositorySession,
    RequestsLoader,
    StoreServiceFactory,
)
from src.app.plugins.store.runtime import (
    PluginStoreRuntimeContext,
    build_plugin_store_runtime_context,
)
from src.app.plugins.store.session import (
    PluginStoreOperationState,
    PluginStoreWindowSession,
)
from src.app.plugins.store.uninstall_flow import PluginStoreUninstallController
from src.app.plugins.ui_event_binding import PluginUiEventBinding
from src.app.startup_metrics import FeatureTimeline
from src.app.ui_feedback import build_ui_notifier
from src.platform.network import load_requests_module
from src.platform.runtime_paths import PLUGIN_DATABASE_FILE
from src.logic.network_downloads import download_api
from src.logic.plugins.store_install.service import DownloadApi
from src.logic.plugins.store_service import PluginStoreService, RequestsModuleProtocol
from src.logic.plugins.uninstall.result import PluginUninstallResult
from src.ui.common.windowing import Toplevel
from src.ui.tabs.plugins.store.cards import StoreCatalogController
from src.ui.tabs.plugins.store.catalog_presenter import (
    PluginStoreCatalogRefreshController,
)
from src.ui.tabs.plugins.store.catalog_view_model import (
    PLUGIN_STORE_ACTION_BUTTON_MIN_WIDTH,
)
from src.ui.tabs.plugins.store.dialogs import prompt_repository_url
from src.ui.tabs.plugins.store.contracts import (
    StoreCompositionProtocol,
    StoreHostPortProtocol,
)
from src.ui.tabs.plugins.store.layout import PluginStoreLayout
from src.ui.tabs.plugins.store.state import PluginStoreViewState
from src.ui.tabs.plugins.store.state_presenter import PluginStoreStateController
from src.ui.tabs.plugins.store.window import MpkStore
from src.app.plugins.store.window_coordinator import PluginStoreWindowController


@dataclass(frozen=True, slots=True)
class PluginStoreUiHostAdapter:
    state: PluginStoreViewState
    is_alive: Callable[[], bool]
    is_plugin_installed: Callable[[str], bool]


@dataclass(frozen=True, slots=True)
class PluginStoreComposition:
    session: PluginStoreWindowSession
    event_binding: PluginUiEventBinding
    repository: PluginStoreRepositorySession
    host_port: PluginStoreHostPort
    catalog: StoreCatalogController
    state_controller: PluginStoreStateController
    install_controller: PluginStoreInstallController
    uninstall_controller: PluginStoreUninstallController
    catalog_refresh: PluginStoreCatalogRefreshController
    fetch_controller: PluginStoreFetchController
    layout: PluginStoreLayout
    controller: PluginStoreWindowController


def focus_existing_plugin_store_window(
    runtime: PluginStoreRuntimeContext,
) -> bool:
    return PluginStoreWindowSession.focus_existing(runtime)


def build_plugin_store_composition(
    window: MpkStore,
    *,
    runtime: PluginStoreRuntimeContext,
    logger: logging.Logger,
    requests_loader: RequestsLoader,
    download_api_func: DownloadApi,
    store_service_factory: StoreServiceFactory,
    move_center_func: Callable[[Toplevel], None] | None = None,
    timeline: FeatureTimeline | None = None,
) -> PluginStoreComposition:
    view_state = window.store_state
    operation_state = PluginStoreOperationState()
    session = PluginStoreWindowSession(
        runtime=runtime,
        window=window,
        logger=logger,
    )
    event_binding = PluginUiEventBinding(
        dispatcher=runtime.dispatcher,
        consume=window._consume_plugin_events,
        is_alive=window.winfo_exists,
        logger=logger,
    )
    repository = PluginStoreRepositorySession(
        settings=runtime.settings,
        temp_path=runtime.temp_path,
        local_db_path=str(PLUGIN_DATABASE_FILE),
        module_manager=runtime.module_manager,
        module_error_codes=runtime.module_error_codes,
        requests_loader=requests_loader,
        download_api_func=download_api_func,
        store_service_factory=store_service_factory,
        logger=logger,
    )

    controller_refs: dict[str, PluginStoreStateController] = {}

    def update_plugin_state(plugin_id: str) -> bool:
        controller = controller_refs.get("state")
        if controller is None:
            raise RuntimeError("Plugin Store state controller is not composed yet.")
        return controller.update_plugin_state(plugin_id)

    def apply_uninstall_result(plugin_id: str, result: PluginUninstallResult) -> None:
        controller = controller_refs.get("state")
        if controller is None:
            raise RuntimeError("Plugin Store state controller is not composed yet.")
        controller.apply_uninstall_result(plugin_id, result)

    host_port = build_plugin_store_host_port(
        window,
        runtime=runtime,
        state=operation_state,
        repository=repository,
        update_plugin_state=update_plugin_state,
        apply_uninstall_result=apply_uninstall_result,
    )
    button_width = PLUGIN_STORE_ACTION_BUTTON_MIN_WIDTH
    ui_host_port = cast(
        StoreHostPortProtocol,
        PluginStoreUiHostAdapter(
            state=view_state,
            is_alive=host_port.is_alive,
            is_plugin_installed=host_port.is_plugin_installed,
        ),
    )
    catalog = StoreCatalogController(
        window,
        texts=lang,
        host_port=ui_host_port,
        button_width=button_width,
        logger=logger,
    )
    notifier = build_ui_notifier(
        runtime.host_window.message_pop,
        host_window=runtime.host_window,
    )
    state_controller = PluginStoreStateController(
        texts=lang,
        host_port=ui_host_port,
        notifier=notifier,
        logger=logger,
    )
    controller_refs["state"] = state_controller
    install_controller = PluginStoreInstallController(
        service_builder=repository.build_install_service,
        host_port=host_port,
        logger=logger,
    )
    uninstall_controller = PluginStoreUninstallController(
        host_port=host_port,
        logger=logger,
    )
    catalog_refresh = PluginStoreCatalogRefreshController(
        texts=lang,
        catalog=catalog,
        state=view_state,
        notifier=notifier,
        is_alive=host_port.is_alive,
        logger=logger,
    )
    fetch_controller = PluginStoreFetchController(
        apply_fetch_result=catalog_refresh.apply_fetch_result,
        host_port=host_port,
        logger=logger,
    )
    layout = PluginStoreLayout(window, texts=lang)
    center_window = move_center_func or (
        lambda target: target.center_on_screen(force=True)
    )

    def request_repository_url(
        current_value: str,
        on_accept: Callable[[str], None],
    ) -> Toplevel:
        return prompt_repository_url(
            parent=window,
            current_value=current_value,
            title=lang.resolve_required_ui_text(keys.REPOSITORY_URL_DIALOG_TITLE),
            ok_text=lang.resolve_required_ui_text(keys.REPOSITORY_URL_CONFIRM_BUTTON),
            cancel_text=lang.resolve_required_ui_text(
                keys.REPOSITORY_URL_CANCEL_BUTTON
            ),
            move_center=center_window,
            on_accept=on_accept,
        )

    controller = PluginStoreWindowController(
        session=session,
        repository=repository,
        state_controller=state_controller,
        install_controller=install_controller,
        uninstall_controller=uninstall_controller,
        fetch_controller=fetch_controller,
        logger=logger,
        build_layout=layout.build,
        center_window=lambda: center_window(window),
        request_repository_url=request_repository_url,
        timeline=timeline,
    )
    return PluginStoreComposition(
        session=session,
        event_binding=event_binding,
        repository=repository,
        host_port=host_port,
        catalog=catalog,
        state_controller=state_controller,
        install_controller=install_controller,
        catalog_refresh=catalog_refresh,
        fetch_controller=fetch_controller,
        uninstall_controller=uninstall_controller,
        layout=layout,
        controller=controller,
    )


def open_plugin_store() -> MpkStore | None:
    runtime = build_plugin_store_runtime_context()
    if focus_existing_plugin_store_window(runtime):
        return None
    timeline = FeatureTimeline("plugin_store_open")
    window = MpkStore(texts=lang)
    composition = build_plugin_store_composition(
        window,
        runtime=runtime,
        logger=logging.getLogger("mio.plugin_store"),
        requests_loader=lambda: cast(RequestsModuleProtocol, load_requests_module()),
        download_api_func=cast(DownloadApi, download_api),
        store_service_factory=PluginStoreService,
        timeline=timeline,
    )
    window.attach(cast(StoreCompositionProtocol, composition))
    window.open()
    timeline.log(logger=logging)
    return window


__all__ = [
    "PluginStoreComposition",
    "build_plugin_store_composition",
    "focus_existing_plugin_store_window",
    "open_plugin_store",
]
