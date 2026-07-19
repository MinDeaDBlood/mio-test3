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


import os
import shutil
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, ".")

from src.app import update as update_module  # noqa: F401 - imported to preserve targeted compatibility surface
from src.app.localization_runtime import LangUtils
from src.ui.tabs.about.click_state import AboutTabClickState
from src.logic.projects.convert import operations as convert_operations
from src.logic.projects.logo.service import (
    LogoRuntimeContext,
    dump_logo as dump_logo_service,
    pack_logo as pack_logo_service,
)
from src.logic.projects.dtbo.service import (
    DtboRuntimeContext,
    pack_dtbo as pack_dtbo_service,
)
from src.logic.projects.pack import registry as pack_registry
from src.logic.projects.pack.boot_images.service import (
    repack_boot as repack_boot_service,
)
from src.logic.projects.project_menu.controller import ProjectMenuController
from src.logic.projects.unpack.boot_images.service import (
    unpack_boot as unpack_boot_service,
)
from src.app.projects.unpack.controller import UnpackWorkspaceController
from src.logic.projects.unpack.workspace_service import UnpackWorkspaceService
from src.app.welcome.controller import WelcomeContentAccess, WelcomeController
from src.platform.welcome_content_repository import WelcomeContentRepository
from src.ui.welcome.navigation_presenter import (
    WelcomeNavigationLabels,
    WelcomeNavigationPresenter,
)
from src.logic.network_downloads import download_api


_TEXTS = LangUtils()
_TEXTS.load_map(
    {
        "plugins_store_button_state_install": "Install",
        "plugins_store_button_state_uninstall": "Uninstall",
        "plugins_store_button_state_ready": "Installing",
        "plugins_store_button_state_installation_complete": "Installed",
        "plugins_store_catalog_view_model_install": "Install",
        "plugins_store_catalog_view_model_uninstall": "Uninstall",
    }
)


def run_all() -> None:
    assert callable(convert_operations.sparse_to_raw)
    assert callable(convert_operations.raw_to_sparse)

    state = AboutTabClickState()
    colors = set()
    triggered = False
    for _ in range(5):
        color, should_open = state.next_color_and_debug(False)
        colors.add(color)
        triggered = triggered or should_open
    assert triggered
    assert all(c.startswith("#") and len(c) == 7 for c in colors)

    assert callable(download_api)

    class _MM:
        def uninstall(self, plugin_id):
            return True, f"removed {plugin_id}", [plugin_id]

        def is_installed(self, _plugin_id):
            return False

    class _Host:
        def __init__(self):
            self.calls = []

        def message_pop(self, *args, **kwargs):
            self.calls.append((args, kwargs))

    from src.ui.tabs.plugins.store.state import PluginStoreSessionState
    from src.ui.tabs.plugins.store.state_presenter import PluginStoreStateController
    from src.app.plugins.store.uninstall_flow import PluginStoreUninstallController

    task_runner = SimpleNamespace(
        run=lambda worker, *args, on_success=None, on_error=None, **kwargs: on_success(
            worker(*args)
        )
        if on_success
        else worker(*args)
    )
    plugin_gateway = _MM()
    host_window = _Host()

    class _Btn:
        def __init__(self):
            self.last = None

        def winfo_exists(self):
            return True

        def config(self, **kwargs):
            self.last = kwargs

    view_state = PluginStoreSessionState()
    view_state.register_controls("demo", _Btn(), _Btn())
    host_port = SimpleNamespace(
        state=view_state,
        plugin_gateway=plugin_gateway,
        notifier=SimpleNamespace(show=host_window.message_pop),
        dispatcher=SimpleNamespace(dispatch=lambda callback, *args: callback(*args)),
        task_runner=task_runner,
        is_alive=lambda: True,
        is_plugin_installed=plugin_gateway.is_installed,
        update_plugin_state=lambda plugin_id: state_controller.update_plugin_state(
            plugin_id
        ),
        apply_uninstall_result=lambda plugin_id,
        result: state_controller.apply_uninstall_result(plugin_id, result),
    )
    state_controller = PluginStoreStateController(
        texts=_TEXTS, host_port=host_port, notifier=host_port.notifier
    )
    uninstall_controller = PluginStoreUninstallController(host_port=host_port)
    uninstall_controller.start("demo")
    assert view_state.controls["demo"][0].last["state"] == "normal"
    assert view_state.controls["demo"][1].last["state"] == "disabled"

    class _WelcomeSettings:
        def __init__(self):
            self.language = "English"
            self.path = "/tmp/workdir"
            self.oobe = "1"

        def set_value(self, key, value):
            setattr(self, key, value)

    with tempfile.TemporaryDirectory() as d:
        lang_dir = Path(d) / "languages"
        lic_dir = Path(d) / "bin" / "licenses"
        lang_dir.mkdir(parents=True)
        lic_dir.mkdir(parents=True)
        (lang_dir / "English.json").write_text("{}")
        (lang_dir / "Russian.json").write_text("{}")
        (lic_dir / "AGPL.txt").write_text("license text")
        (lic_dir / "private.txt").write_text("private note")
        ws = _WelcomeSettings()
        repository = WelcomeContentRepository(
            language_directory=lang_dir,
            license_directory=lic_dir,
        )
        page = WelcomeController(
            settings=ws,
            content_service=WelcomeContentAccess(
                list_languages=repository.list_languages,
                list_licenses=repository.list_licenses,
                read_license=repository.read_license,
                read_private_notice=repository.read_private_notice,
            ),
            current_language=lambda: ws.language,
            frame_count=6,
        )
        main_spec = page.main_data()
        assert main_spec.languages == ("English", "Russian")
        assert page.workdir_data().workdir == "/tmp/workdir"
        chosen = page.set_workdir("/new/path")
        assert chosen == "/new/path" and ws.path == "/new/path"
        license_spec = page.license_data()
        assert license_spec.selected_license == "AGPL"
        assert page.read_private_notice() == "private note"

    nav_settings = _WelcomeSettings()
    nav_repository = WelcomeContentRepository(
        language_directory="languages",
        license_directory="bin/licenses",
    )
    nav = WelcomeController(
        settings=nav_settings,
        content_service=WelcomeContentAccess(
            list_languages=nav_repository.list_languages,
            list_licenses=nav_repository.list_licenses,
            read_license=nav_repository.read_license,
            read_private_notice=nav_repository.read_private_notice,
        ),
        current_language=lambda: nav_settings.language,
        frame_count=6,
    )
    assert nav.initial_step() == 1
    assert nav.persist_step(99) == 5
    nav_state = WelcomeNavigationPresenter.build_state(
        step=5,
        frame_count=6,
        labels=WelcomeNavigationLabels(back="Back", next="Next", finish="Finish"),
    )
    assert (
        nav_state.is_last and nav_state.next_text == "Finish" and nav_state.back_enabled
    )

    class _PMgr:
        def __init__(self):
            self.base = tempfile.mkdtemp()

        def get_projects(self):
            return sorted(p.name for p in Path(self.base).iterdir() if p.is_dir())

        def exist(self, name=None):
            return bool(name) and Path(self.get_work_path(name)).exists()

        def get_work_path(self, name):
            return os.path.join(self.base, name)

        def new(self, name):
            os.makedirs(self.get_work_path(name), exist_ok=True)

        def remove(self, name):
            shutil.rmtree(self.get_work_path(name), ignore_errors=True)

    _current = {"name": "Alpha"}
    pm = _PMgr()
    os.makedirs(pm.get_work_path("Alpha"), exist_ok=True)
    controller = ProjectMenuController(
        project_manager=pm,
        current_project_getter=lambda: _current["name"],
        current_project_setter=lambda v: _current.__setitem__("name", v),
    )
    refresh = controller.refresh_projects()
    assert refresh.projects == ("Alpha",) and refresh.selected_project == "Alpha"
    created = controller.create_new("Beta", invalid_message="bad")
    assert created.succeeded and "Beta" in created.projects
    renamed = controller.rename_current(
        "Gamma",
        exists_message="exists",
        unchanged_message="same",
        missing_message="missing",
    )
    assert renamed.succeeded and _current["name"] == "Gamma" and pm.exist("Gamma")
    removed = controller.remove_current(missing_message="missing")
    assert removed.succeeded and _current["name"] == "Beta"
    shutil.rmtree(pm.base, ignore_errors=True)

    formats = pack_registry.get_output_formats()
    assert {"raw", "sparse", "dat", "br"}.issubset(set(formats))

    assert not Path("src/app/tk_runtime.py").exists()
    assert not Path("src/core/utils.py").exists()

    class _PMForUnpack:
        def __init__(self, work):
            self.work = work

        def exist(self):
            return True

        def current_work_path(self):
            return self.work

    with tempfile.TemporaryDirectory() as d:
        calls = []
        workspace_service = UnpackWorkspaceService(
            json_edit_cls=lambda p: None,
            gettype_func=lambda p: "img",
        )
        ctl = UnpackWorkspaceController(
            project_manager=_PMForUnpack(d + os.sep),
            workspace_service=workspace_service,
            unpack_func=lambda selected, fmt: calls.append((list(selected), fmt))
            or True,
        )
        ok, refresh_mode = ctl.execute_unpack_selection(["system"], "payload")
        assert ok is True and refresh_mode == "payload_candidates"
        assert calls == [(["system"], "payload")]
        ok2, refresh_mode2 = ctl.execute_unpack_selection([], "img")
        assert ok2 is False and refresh_mode2 == "auto"

    class _LogoDumper:
        calls = []

        def __init__(self, *args):
            self.args = args

        def unpack(self):
            _LogoDumper.calls.append(("unpack", self.args))

        def repack(self):
            _LogoDumper.calls.append(("repack", self.args))

    with tempfile.TemporaryDirectory() as d:
        work = Path(d)
        dtbo_root = work / "dtbo"
        dts_dir = dtbo_root / "dts"
        dts_dir.mkdir(parents=True)
        (dts_dir / "dts.10").write_text("a")
        (dts_dir / "dts.2").write_text("b")
        commands = []
        created = {}

        def _dtc_call(cmd, out=False):
            commands.append(cmd)
            Path(cmd[-1]).write_text("compiled")
            return 0

        ok = pack_dtbo_service(
            runtime=DtboRuntimeContext(
                work_path=str(work),
                output_path=str(work / "out"),
                output=SimpleNamespace(
                    log=lambda *args, **kwargs: None,
                    notify=lambda *args, **kwargs: None,
                ),
            ),
            exists_func=lambda p: Path(p).exists(),
            listdir_func=lambda p: sorted(os.listdir(p)),
            call_func=_dtc_call,
            create_func=lambda out, images, page_size: created.update(
                {"out": out, "images": list(images), "page_size": page_size}
            ),
            re_folder_func=lambda p: Path(p).mkdir(parents=True, exist_ok=True),
            rmdir_func=lambda p, quiet=False: shutil.rmtree(p, ignore_errors=True),
        )
        assert ok is True
        assert commands and commands[0][0] == "dtc"
        assert (
            created["images"][-1].endswith("dtbo.10") and created["page_size"] == 4096
        )

    with tempfile.TemporaryDirectory() as d:
        work = Path(d)
        (work / "logo").mkdir()
        (work / "logo.img").write_text("origin")
        (work / "logo-new.img").write_text("new")
        ctx = LogoRuntimeContext(
            work_path=str(work),
            output=SimpleNamespace(
                log=lambda *args, **kwargs: None, notify=lambda *args, **kwargs: None
            ),
        )
        assert (
            dump_logo_service(
                str(work / "logo.img"),
                runtime=ctx,
                dumper_cls=_LogoDumper,
                re_folder_func=lambda p: Path(p).mkdir(parents=True, exist_ok=True),
            )
            is True
        )
        result = pack_logo_service(
            runtime=ctx,
            dumper_cls=_LogoDumper,
            findfile_func=lambda name, root: str(work / name),
            rmdir_func=lambda p, quiet=False: shutil.rmtree(p, ignore_errors=True),
        )
        assert result == 0 and (work / "logo.img").exists()

    assert callable(repack_boot_service)
    assert callable(unpack_boot_service)


def test_public_contract_regressions() -> None:
    run_all()

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
