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
from src.app.plugins.store.session import PluginStoreOperationState
from src.logic.plugins.store_service import PluginStoreFetchResult
from src.ui.tabs.plugins.store.catalog_presenter import (
    PluginStoreCatalogRefreshController,
)
from src.ui.tabs.plugins.store.state import PluginStoreViewState
from tests.support.plugin_catalog import plugin_item


def _build_texts() -> LangUtils:
    texts = LangUtils()
    texts.load_map(
        {
            "plugins_store_catalog_repository_parse_error_message": "Repository parse error",
            "plugins_store_catalog_repository_parse_error_dialog_title": "Repository error",
        }
    )
    return texts


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
        worker, args, on_success, _on_error = self.pending.pop(0)
        result = worker(*args)
        if on_success:
            return on_success(result)
        return result


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


class _Window:
    def __init__(self, *, task_runner: _TaskRunner | None = None):
        self.store_state = PluginStoreViewState(catalog=[plugin_item("cached")])
        self.operation_state = PluginStoreOperationState()
        self.runtime = SimpleNamespace(task_runner=task_runner or _TaskRunner())
        self.repository = SimpleNamespace(
            repo="repo://initial",
            build_fetch_service=lambda: _FetchService(
                PluginStoreFetchResult(items=(plugin_item("built"),))
            ),
            fetch=lambda refresh=False: PluginStoreFetchResult(
                items=(plugin_item("repo-fetch"),)
            ),
        )
        self.alive = True
        self.messages: list[tuple] = []

    def winfo_exists(self):
        return self.alive

    def message_pop(self, *args, **kwargs):
        self.messages.append((args, kwargs))


def _host_port(window):
    return SimpleNamespace(
        state=window.operation_state,
        repository=window.repository,
        notifier=SimpleNamespace(show=window.message_pop),
        task_runner=window.runtime.task_runner,
        is_alive=window.winfo_exists,
    )


def _catalog_refresh(window, catalog):
    return PluginStoreCatalogRefreshController(
        texts=_build_texts(),
        catalog=catalog,
        state=window.store_state,
        notifier=SimpleNamespace(show=window.message_pop),
        is_alive=window.winfo_exists,
    )


def test_fetch_refresh_uses_repository_service_and_inflight_guard() -> None:
    task_runner = _TaskRunner(defer=True)
    window = _Window(task_runner=task_runner)
    service = _FetchService(PluginStoreFetchResult(items=(plugin_item("fresh"),)))
    window.repository.fetch = service.fetch
    catalog = _Catalog()
    controller = PluginStoreFetchController(
        apply_fetch_result=_catalog_refresh(window, catalog).apply_fetch_result,
        host_port=_host_port(window),
    )

    assert controller.request_refresh(False) is True
    assert controller.request_refresh(True) is False
    assert window.operation_state.fetch_inflight is True
    assert len(task_runner.calls) == 1

    task_runner.flush_success()

    expected = (plugin_item("fresh"),)
    assert service.calls == [False]
    assert window.operation_state.fetch_inflight is False
    assert window.store_state.catalog_items() == expected
    assert catalog.calls == [("clear", None), ("add_app", expected)]


def test_fetch_runner_failure_is_normalized_and_clears_inflight() -> None:
    window = _Window(task_runner=_TaskRunner(fail_run=RuntimeError("runner boom")))
    catalog = _Catalog()
    controller = PluginStoreFetchController(
        apply_fetch_result=_catalog_refresh(window, catalog).apply_fetch_result,
        host_port=_host_port(window),
    )

    assert controller.request_refresh(False) is False
    assert window.operation_state.fetch_inflight is False
    assert window.messages
    assert window.store_state.catalog_items() == ()
    assert catalog.calls == [("clear", None), ("add_app", ())]


def test_initial_refresh_initializes_repository_inside_worker() -> None:
    task_runner = _TaskRunner(defer=True)
    window = _Window(task_runner=task_runner)
    catalog = _Catalog()
    initialized: list[bool] = []
    controller = PluginStoreFetchController(
        apply_fetch_result=_catalog_refresh(window, catalog).apply_fetch_result,
        host_port=_host_port(window),
    )

    assert controller.request_initial_refresh(lambda: initialized.append(True)) is True
    assert initialized == []

    task_runner.flush_success()

    assert initialized == [True]
    assert window.operation_state.fetch_inflight is False


def test_catalog_refresh_replaces_view_state_before_rendering() -> None:
    window = _Window()
    catalog = _Catalog()
    refresh = _catalog_refresh(window, catalog)
    result = PluginStoreFetchResult(items=(plugin_item("fresh", name="Fresh"),))

    assert refresh.apply_fetch_result(result) is True
    assert window.store_state.catalog_items() == result.items
    assert catalog.calls == [("clear", None), ("add_app", result.items)]


def test_view_state_contains_only_presentation_state() -> None:
    state = PluginStoreViewState()
    assert not hasattr(state, "store_service")
    assert not hasattr(state, "set_repository_context")
    assert not hasattr(state, "current_store_service")
    assert not hasattr(state, "start_task")
    assert not hasattr(state, "start_fetch")
    assert not hasattr(state, "repository_items")
    assert not hasattr(state, "plugin_info_for")


if __name__ == "__main__":
    test_fetch_refresh_uses_repository_service_and_inflight_guard()
    test_fetch_runner_failure_is_normalized_and_clears_inflight()
    test_initial_refresh_initializes_repository_inside_worker()
    test_catalog_refresh_replaces_view_state_before_rendering()
    test_view_state_contains_only_presentation_state()
    print("PLUGIN_STORE_FETCH_REFRESH_TESTS_OK")
