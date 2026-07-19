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


from types import SimpleNamespace



from src.app.localization_runtime import LangUtils
from src.app.plugins.store.fetch_flow import PluginStoreFetchController
from src.app.plugins.store.install_flow import PluginStoreInstallController
from src.app.plugins.store.session import PluginStoreOperationState
from src.app.plugins.store.uninstall_flow import PluginStoreUninstallController
from src.app.plugins.ui_event_binding import PluginUiEventBinding
from src.logic.plugins.events import PluginStateChangedEvent, plugin_event_bus
from src.logic.plugins.store_install import StoreInstallResult
from src.logic.plugins.store_service import PluginStoreFetchResult
from src.ui.tabs.plugins.store.catalog_presenter import (
    PluginStoreCatalogRefreshController,
)
from src.ui.tabs.plugins.store.state import PluginStoreViewState
from src.ui.tabs.plugins.store.state_presenter import PluginStoreStateController
from tests.support.plugin_catalog import plugin_item


def _build_texts() -> LangUtils:
    texts = LangUtils()
    texts.load_map(
        {
            "plugins_store_button_state_install": "Install",
            "plugins_store_button_state_uninstall": "Uninstall",
            "plugins_store_button_state_ready": "Installing",
            "plugins_store_button_state_installation_complete": "Installed",
            "plugins_store_catalog_view_model_install": "Install",
            "plugins_store_catalog_view_model_uninstall": "Uninstall",
            "plugins_store_catalog_repository_parse_error_message": "Repository parse error",
            "plugins_store_catalog_repository_parse_error_dialog_title": "Repository error",
            "plugins_store_install_dependency_not_found_message_format": "Cannot install {plugin_name}: missing {dep_name}",
            "plugins_store_install_dependency_not_found_dialog_title": "Dependency not found",
            "plugins_store_install_dependency_failed_message_format": "Cannot install {plugin_name}: dependency {dep_name} failed",
            "plugins_store_install_dependency_failed_dialog_title": "Dependency installation failed",
            "plugins_store_install_plugin_failed_message_format": "Failed to install {plugin_name}: {reason_text}",
            "plugins_store_install_plugin_failed_dialog_title": "Plugin installation failed",
            "plugins_store_install_download_failed_label": "Download failed",
            "plugins_store_install_download_error_dialog_title": "Download error",
            "plugins_store_uninstall_error_dialog_title": "Uninstall error",
        }
    )
    return texts


class _Button:
    def __init__(self):
        self.calls: list[dict] = []
        self.alive = True

    def winfo_exists(self):
        return self.alive

    def config(self, **kwargs):
        self.calls.append(kwargs)


class _Dispatcher:
    def __init__(self):
        self.calls: list[tuple] = []

    def dispatch(self, callback, *args):
        self.calls.append((callback, args))
        callback(*args)
        return True


class _TaskRunner:
    def __init__(self, *, defer: bool = False, fail_run: Exception | None = None):
        self.defer = defer
        self.fail_run = fail_run
        self.calls: list[tuple] = []
        self.pending: list[tuple] = []

    def run(self, worker, *args, on_success=None, on_error=None):
        self.calls.append((worker, args, on_success, on_error))
        if self.fail_run is not None:
            raise self.fail_run
        if self.defer:
            self.pending.append((worker, args, on_success, on_error))
            return True
        try:
            result = worker(*args)
        except Exception as exc:
            if on_error:
                return on_error(exc)
            raise
        if on_success:
            return on_success(result)
        return result

    def flush_success(self):
        worker, args, on_success, on_error = self.pending.pop(0)
        try:
            result = worker(*args)
        except Exception as exc:
            if on_error:
                return on_error(exc)
            raise
        if on_success:
            return on_success(result)
        return result


class _PluginGateway:
    def __init__(self):
        self.installed: dict[str, bool] = {"demo": False, "other": False}
        self.uninstall_calls: list[str] = []
        self.uninstall_result = (True, "removed", ["demo"])
        self.fail_uninstall: Exception | None = None

    def is_installed(self, plugin_id):
        return bool(self.installed.get(plugin_id, False))

    def uninstall(self, plugin_id):
        self.uninstall_calls.append(plugin_id)
        if self.fail_uninstall is not None:
            raise self.fail_uninstall
        self.installed[plugin_id] = False
        return self.uninstall_result


class _Catalog:
    def __init__(self):
        self.calls: list[tuple] = []

    def clear(self):
        self.calls.append(("clear", None))

    def add_app(self, items):
        self.calls.append(("add_app", tuple(items)))


class _FetchService:
    def __init__(self, result):
        self.result = result
        self.calls: list[bool] = []

    def fetch(self, *, refresh=False):
        self.calls.append(refresh)
        return self.result


class _InstallService:
    def __init__(self, result, *, fail: Exception | None = None):
        self.result = result
        self.fail = fail
        self.calls: list[dict] = []

    def install_from_repo(self, **kwargs):
        self.calls.append(kwargs)
        kwargs["progress_callback"](42)
        if self.fail is not None:
            raise self.fail
        return self.result


class _Window:
    def __init__(self, *, task_runner: _TaskRunner | None = None):
        self.store_state = PluginStoreViewState(
            catalog=[
                plugin_item(
                    "demo", name="Demo Plugin", files=("demo.zip",), size_bytes=123
                ),
                plugin_item("other", name="Other Plugin"),
            ]
        )
        self.store_state.register_controls("demo", _Button(), _Button())
        self.store_state.register_controls("other", _Button(), _Button())
        self.operation_state = PluginStoreOperationState()
        self.dispatcher = _Dispatcher()
        self.task_runner = task_runner or _TaskRunner()
        self.plugin_gateway = _PluginGateway()
        self.alive = True
        self.messages: list[tuple] = []
        self.catalog_calls: list[tuple] = []
        self.refresh_requests: list[bool] = []
        repository_items = self.store_state.catalog_items()
        self.repository = SimpleNamespace(
            repo="repo://initial",
            build_fetch_service=lambda: _FetchService(
                PluginStoreFetchResult(items=repository_items)
            ),
            fetch=lambda refresh=False: PluginStoreFetchResult(items=repository_items),
            repository_items=lambda: repository_items,
            plugin_info_for=lambda plugin_id: next(
                (item for item in repository_items if item.plugin_id == plugin_id),
                None,
            ),
        )
        self.host_port = SimpleNamespace(
            state=self.operation_state,
            plugin_gateway=self.plugin_gateway,
            repository=self.repository,
            notifier=SimpleNamespace(show=self.message_pop),
            dispatcher=self.dispatcher,
            task_runner=self.task_runner,
            is_alive=self.winfo_exists,
            is_plugin_installed=self.plugin_gateway.is_installed,
            update_plugin_state=lambda plugin_id: self.state_controller.update_plugin_state(
                plugin_id
            ),
            apply_uninstall_result=lambda plugin_id,
            result: self.state_controller.apply_uninstall_result(plugin_id, result),
        )
        self.ui_host_port = SimpleNamespace(
            state=self.store_state,
            is_alive=self.winfo_exists,
            is_plugin_installed=self.plugin_gateway.is_installed,
        )
        self.state_controller = PluginStoreStateController(
            texts=_build_texts(),
            host_port=self.ui_host_port,
            notifier=self.host_port.notifier,
        )

    def winfo_exists(self):
        return self.alive

    def message_pop(self, *args, **kwargs):
        self.messages.append((args, kwargs))

    def request_db_refresh(self, refresh=False):
        self.refresh_requests.append(refresh)

    def consume_plugin_events(self, events):
        return self.state_controller.consume_events(events)


def _start_install(window: _Window, service: _InstallService, *, host_port=None):
    active_port = host_port or window.host_port
    controller = PluginStoreInstallController(
        service_builder=lambda: service,
        host_port=active_port,
    )
    return controller.start(
        ("demo.zip",),
        123,
        "demo",
        (),
        on_started=window.state_controller.mark_installing,
        on_progress=window.state_controller.update_install_progress,
        on_finished=window.state_controller.apply_install_result,
    )


def test_plugin_store_view_state_owns_only_presentation_state() -> None:
    item = plugin_item("demo")
    state = PluginStoreViewState(catalog=[item])
    install = _Button()
    uninstall = _Button()
    state.register_controls("demo", install, uninstall)

    assert state.catalog_items() == (item,)
    assert state.controls_for("demo") == (install, uninstall)
    assert state.visible_plugin_ids() == ("demo",)
    assert not hasattr(state, "tasks")
    assert not hasattr(state, "fetch_inflight")
    assert not hasattr(state, "start_task")
    assert not hasattr(state, "start_fetch")
    assert not hasattr(state, "repository_items")
    assert not hasattr(state, "plugin_info_for")

    operation_state = PluginStoreOperationState()
    assert operation_state.start_task("demo") is True
    assert operation_state.start_task("demo") is False
    assert operation_state.finish_task("demo") is True
    assert operation_state.finish_task("demo") is False
    assert operation_state.start_fetch() is True
    assert operation_state.start_fetch() is False
    assert operation_state.finish_fetch() is True


def test_install_success_dispatches_progress_updates_button_state_and_cleans_task() -> (
    None
):
    window = _Window()
    window.plugin_gateway.installed["demo"] = True
    service = _InstallService(StoreInstallResult(True, "demo"))
    _start_install(window, service)

    assert window.operation_state.tasks == set()
    assert service.calls[0]["repository_items"][0].plugin_id == "demo"
    install_button, uninstall_button = window.store_state.controls["demo"]
    assert any(call.get("text") == "42 %" for call in install_button.calls)
    assert install_button.calls[-1]["state"] == "disabled"
    assert uninstall_button.calls[-1]["state"] == "normal"
    assert window.dispatcher.calls


def test_install_failure_shows_message_restores_button_state_and_cleans_task() -> None:
    window = _Window()
    service = _InstallService(
        StoreInstallResult(
            False,
            "demo",
            error_kind="install-error",
            error_reason="boom",
        )
    )
    _start_install(window, service)

    assert window.operation_state.tasks == set()
    assert window.messages
    install_button, uninstall_button = window.store_state.controls["demo"]
    assert install_button.calls[-1]["state"] == "normal"
    assert uninstall_button.calls[-1]["state"] == "disabled"


def test_install_finalize_uses_host_port_update_callback_instead_of_window_method() -> (
    None
):
    window = _Window()
    window.plugin_gateway.installed["demo"] = True
    service = _InstallService(StoreInstallResult(True, "demo"))
    updates: list[str] = []
    host_port = SimpleNamespace(
        state=window.operation_state,
        plugin_gateway=window.plugin_gateway,
        repository=window.repository,
        notifier=window.host_port.notifier,
        dispatcher=window.dispatcher,
        task_runner=window.task_runner,
        is_alive=window.winfo_exists,
        is_plugin_installed=window.plugin_gateway.is_installed,
        update_plugin_state=updates.append,
        apply_uninstall_result=lambda plugin_id, result: None,
    )
    _start_install(window, service, host_port=host_port)
    assert updates == ["demo"]


def test_uninstall_flow_uses_host_port_apply_callback() -> None:
    window = _Window()
    applied: list[tuple[str, object]] = []
    host_port = SimpleNamespace(
        state=window.operation_state,
        plugin_gateway=window.plugin_gateway,
        repository=window.repository,
        notifier=window.host_port.notifier,
        dispatcher=window.dispatcher,
        task_runner=window.task_runner,
        is_alive=window.winfo_exists,
        is_plugin_installed=window.plugin_gateway.is_installed,
        update_plugin_state=lambda plugin_id: None,
        apply_uninstall_result=lambda plugin_id, result: applied.append(
            (plugin_id, result)
        ),
    )
    PluginStoreUninstallController(host_port=host_port).start("demo")
    assert applied == [("demo", window.plugin_gateway.uninstall_result)]


def test_fetch_lifecycle_uses_view_state_and_blocks_duplicate_refresh() -> None:
    task_runner = _TaskRunner(defer=True)
    window = _Window(task_runner=task_runner)
    fresh = plugin_item("fresh")
    service = _FetchService(PluginStoreFetchResult(items=(fresh,)))
    window.repository.fetch = service.fetch
    catalog = _Catalog()
    refresh = PluginStoreCatalogRefreshController(
        texts=_build_texts(),
        catalog=catalog,
        state=window.store_state,
        notifier=window.host_port.notifier,
        is_alive=window.winfo_exists,
    )
    controller = PluginStoreFetchController(
        apply_fetch_result=refresh.apply_fetch_result,
        host_port=window.host_port,
    )

    assert controller.request_refresh(False) is True
    assert window.operation_state.fetch_inflight is True
    assert controller.request_refresh(True) is False
    assert len(task_runner.calls) == 1

    task_runner.flush_success()

    assert window.operation_state.fetch_inflight is False
    assert service.calls == [False]
    assert window.store_state.catalog_items() == (fresh,)
    assert catalog.calls == [("clear", None), ("add_app", (fresh,))]


def test_fetch_task_runner_failure_is_normalized_and_clears_inflight() -> None:
    window = _Window(task_runner=_TaskRunner(fail_run=RuntimeError("runner boom")))
    catalog = _Catalog()
    controller = PluginStoreFetchController(
        apply_fetch_result=PluginStoreCatalogRefreshController(
            texts=_build_texts(),
            catalog=catalog,
            state=window.store_state,
            notifier=window.host_port.notifier,
            is_alive=window.winfo_exists,
        ).apply_fetch_result,
        host_port=window.host_port,
    )

    assert controller.request_refresh(False) is False
    assert window.operation_state.fetch_inflight is False
    assert window.messages
    assert catalog.calls == [("clear", None), ("add_app", ())]


def test_uninstall_success_updates_only_button_state_without_catalog_refresh() -> None:
    window = _Window()
    window.plugin_gateway.installed["demo"] = True
    PluginStoreUninstallController(host_port=window.host_port).start("demo")

    assert window.plugin_gateway.uninstall_calls == ["demo"]
    assert window.refresh_requests == []
    install_button, uninstall_button = window.store_state.controls["demo"]
    assert install_button.calls[-1]["state"] == "normal"
    assert uninstall_button.calls[-1]["state"] == "disabled"


def test_uninstall_failure_shows_message_and_keeps_buttons_consistent() -> None:
    window = _Window()
    window.plugin_gateway.installed["demo"] = True
    window.plugin_gateway.fail_uninstall = RuntimeError("uninstall boom")
    PluginStoreUninstallController(host_port=window.host_port).start("demo")

    assert window.messages
    install_button, uninstall_button = window.store_state.controls["demo"]
    assert install_button.calls[-1]["state"] == "disabled"
    assert uninstall_button.calls[-1]["state"] == "normal"


def test_plugin_event_binding_coalesces_to_targeted_store_state_update() -> None:
    window = _Window()
    window.plugin_gateway.installed["demo"] = True
    demo_install, demo_uninstall = window.store_state.controls["demo"]
    other_install, other_uninstall = window.store_state.controls["other"]

    binding = PluginUiEventBinding(
        dispatcher=window.dispatcher,
        consume=window.consume_plugin_events,
        is_alive=window.winfo_exists,
    )
    try:
        plugin_event_bus.publish(
            PluginStateChangedEvent(
                plugin_id="demo",
                refresh_manager=False,
                refresh_store=True,
            )
        )
    finally:
        binding.close()

    assert demo_install.calls[-1]["state"] == "disabled"
    assert demo_uninstall.calls[-1]["state"] == "normal"
    assert other_install.calls == []
    assert other_uninstall.calls == []


def test_catalog_refresh_replaces_view_state_instead_of_fetch_flow_mutation() -> None:
    window = _Window()
    catalog = _Catalog()
    refresh = PluginStoreCatalogRefreshController(
        texts=_build_texts(),
        catalog=catalog,
        state=window.store_state,
        notifier=window.host_port.notifier,
        is_alive=window.winfo_exists,
    )

    result = PluginStoreFetchResult(items=(plugin_item("fresh", name="Fresh Plugin"),))
    assert refresh.apply_fetch_result(result) is True
    assert window.store_state.catalog_items() == result.items
    assert catalog.calls == [("clear", None), ("add_app", result.items)]


if __name__ == "__main__":
    test_plugin_store_view_state_owns_only_presentation_state()
    test_install_success_dispatches_progress_updates_button_state_and_cleans_task()
    test_install_failure_shows_message_restores_button_state_and_cleans_task()
    test_install_finalize_uses_host_port_update_callback_instead_of_window_method()
    test_uninstall_flow_uses_host_port_apply_callback()
    test_fetch_lifecycle_uses_view_state_and_blocks_duplicate_refresh()
    test_fetch_task_runner_failure_is_normalized_and_clears_inflight()
    test_uninstall_success_updates_only_button_state_without_catalog_refresh()
    test_uninstall_failure_shows_message_and_keeps_buttons_consistent()
    test_plugin_event_binding_coalesces_to_targeted_store_state_update()
    test_catalog_refresh_replaces_view_state_instead_of_fetch_flow_mutation()
    print("PLUGIN_STORE_LIFECYCLE_BOUNDARY_TESTS_OK")
