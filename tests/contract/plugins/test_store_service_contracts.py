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


from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import json
import sys
from pathlib import Path
from threading import Thread
from types import SimpleNamespace

import requests

sys.path.insert(0, ".")

from src.core.json_store import JsonEdit
from src.logic.network_downloads import download_api
from src.logic.plugins.models import ModuleErrorCodes
from src.logic.plugins.module_manager import ModuleManager
from src.logic.plugins.store_install.service import StorePluginInstallService
from src.logic.plugins.store_service import PluginStoreService
from tests.support.plugin_catalog import plugin_item


class _QuietHttpHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *_args: object) -> None:
        return None


@contextmanager
def _serve_repository(directory: Path):
    handler = partial(_QuietHttpHandler, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _create_mpk(path: Path, plugin_id: str, *, dependencies: tuple[str, ...] = ()) -> None:
    import zipfile

    resources = BytesIO()
    with zipfile.ZipFile(resources, "w") as archive:
        archive.writestr("main.sh", f"echo {plugin_id}\n")
    info = (
        "[module]\n"
        f"identifier = {plugin_id}\n"
        f"name = {plugin_id}\n"
        "version = 1.0\n"
        "author = MIO tests\n"
        "describe = Local integration package\n"
        "resource = resources.zip\n"
        "system = all\n"
        "arch = all\n"
        f"depend = {' '.join(dependencies)}\n"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("info", info)
        archive.writestr("resources.zip", resources.getvalue())


def test_plugin_store_uses_real_http_json_storage_download_and_install(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    dependency_mpk = repository / "dep-one.mpk"
    main_mpk = repository / "demo-main.mpk"
    _create_mpk(dependency_mpk, "dep-one")
    _create_mpk(main_mpk, "demo-main", dependencies=("dep-one",))
    repository_items = (
        plugin_item(
            "dep-one",
            files=(dependency_mpk.name,),
            size_bytes=dependency_mpk.stat().st_size,
        ),
        plugin_item(
            "demo-main",
            files=(main_mpk.name,),
            size_bytes=main_mpk.stat().st_size,
            dependencies=("dep-one",),
        ),
    )
    (repository / "plugin.json").write_text(
        json.dumps([item.to_mapping() for item in repository_items]),
        encoding="utf-8",
    )

    cache_path = tmp_path / "plugin_db.json"
    JsonEdit(str(cache_path)).write([plugin_item("cached").to_mapping()])
    module_manager = ModuleManager(module_dir=tmp_path / "installed")
    progress: list[int] = []

    with _serve_repository(repository) as repo_url:
        catalog = PluginStoreService(
            repo_url=repo_url,
            local_db_path=str(cache_path),
            json_edit_cls=JsonEdit,
            requests_module=requests,
        )
        assert catalog.fetch(refresh=False).items == (plugin_item("cached"),)

        refreshed = catalog.fetch(refresh=True)
        assert refreshed.items == repository_items
        assert JsonEdit(str(cache_path)).read() == [
            item.to_mapping() for item in repository_items
        ]

        install = StorePluginInstallService(
            repo_url=repo_url,
            temp_path=str(tmp_path / "downloads"),
            plugin_install_port=module_manager,
            module_error_codes=ModuleErrorCodes,
            download_api_func=download_api,
        ).install_from_repo(
            plugin_id="demo-main",
            files=(main_mpk.name,),
            size=main_mpk.stat().st_size,
            depends=("dep-one",),
            repository_items=repository_items,
            progress_callback=progress.append,
        )

    assert install.ok is True
    assert module_manager.is_installed("dep-one")
    assert module_manager.is_installed("demo-main")
    assert (tmp_path / "installed" / "dep-one" / "main.sh").is_file()
    assert (tmp_path / "installed" / "demo-main" / "main.sh").is_file()
    assert progress and progress[-1] == 100

    offline = PluginStoreService(
        repo_url=repo_url,
        local_db_path=str(cache_path),
        json_edit_cls=JsonEdit,
        requests_module=requests,
    ).fetch(refresh=True)
    assert offline.ok is False
    assert offline.error_text


_TEXTS = SimpleNamespace(
    plugins_store_button_state_install="Install",
    plugins_store_button_state_uninstall="Uninstall",
    plugins_store_button_state_ready="Installing",
    plugins_store_button_state_installation_complete="Installed",
    plugins_store_catalog_view_model_install="Install",
    plugins_store_catalog_view_model_uninstall="Uninstall",
    resolve=lambda *keys, default="": default or keys[0],
)


def test_plugin_store_catalog_uses_surface_boundary() -> None:
    from src.ui.tabs.plugins.store.cards import StoreCatalogController

    calls: list[tuple[str, str | None]] = []

    class Frame:
        def __init__(self, exists=True, mapped=False):
            self.exists = exists
            self.mapped = mapped

        def winfo_exists(self):
            return self.exists

        def winfo_ismapped(self):
            return self.mapped

    class State:
        def app_info_ids(self):
            return ("demo",)

        def catalog_items(self):
            return (plugin_item("demo", name="Demo"),)

        def app_info_items(self):
            return (("demo", Frame(mapped=False)),)

        def app_frame_for(self, plugin_id):
            return None

        def set_app_frame(self, plugin_id, frame):
            calls.append(("set_frame", plugin_id))

        def register_controls(self, plugin_id, install_button, uninstall_button):
            calls.append(("register_controls", plugin_id))

        def clear_catalog_widgets(self):
            calls.append(("clear", None))

        def controls_for(self, plugin_id):
            return None

    class Surface:
        def search_text(self):
            calls.append(("search", None))
            return "demo"

        def show_card(self, frame):
            calls.append(("show", None))

        def hide_card(self, frame):
            calls.append(("hide", None))

        def sync_after_search(self):
            calls.append(("sync_search", None))

        def pack_card(self, frame):
            calls.append(("pack", None))

        def clear_card_widgets(self):
            calls.append(("clear_widgets", None))

        def sync_after_catalog_update(self):
            calls.append(("sync_catalog", None))

    host_port = SimpleNamespace(
        state=State(),
        is_alive=lambda: True,
        is_plugin_installed=lambda plugin_id: False,
    )
    controller = StoreCatalogController(
        SimpleNamespace(),
        texts=_TEXTS,
        host_port=host_port,
        button_width=12,
        catalog_surface=Surface(),
    )
    controller.search_apps()
    assert ("search", None) in calls
    assert ("show", None) in calls
    assert ("sync_search", None) in calls


def test_plugin_store_fetch_uses_host_port_repository() -> None:
    from src.app.plugins.store.fetch_flow import PluginStoreFetchController

    calls: list[tuple[str, object]] = []

    class Repository:
        def fetch(self, refresh=False):
            calls.append(("fetch", refresh))
            return "result"

    host_port = SimpleNamespace(repository=Repository())
    controller = PluginStoreFetchController(
        apply_fetch_result=lambda _result: True,
        host_port=host_port,
    )
    assert controller.fetch_db(refresh=True) == "result"
    assert calls == [("fetch", True)]


if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
