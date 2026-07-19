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


import sys

sys.path.insert(0, ".")

import json
import os
import tempfile
import zipfile
from pathlib import Path
from types import SimpleNamespace

from src.app.localization_runtime import LangUtils
from src.app.update_controller import UpdateWorkflowController
from src.ui.update.presenter import UpdatePresentationController
from src.logic.update.install_service import (
    apply_staged_update,
    build_updater_path,
    cleanup_completed_update,
    prepare_update_payload,
)
from src.logic.update.service import (
    UpdateFetchError,
    fetch_release_check,
    select_release_asset,
)
from src.logic.update.models import PreparedUpdatePayload
from src.app.update_orchestrator import (
    PendingUpdateMode,
    UpdateOrchestrator,
    detect_pending_update_mode,
)


def _exercise_update_logic_boundary() -> None:
    class _FakeResponse:
        text = json.dumps(
            {
                "name": "v2.0.0",
                "body": "changes",
                "assets": [
                    {
                        "name": "v2.0.0-linux.zip",
                        "browser_download_url": "https://example.invalid/linux.zip",
                        "size": 42,
                        "download_count": 7,
                    }
                ],
            }
        )

    class _FakeRequests:
        def get(self, url):
            assert url == "https://example.invalid/releases/latest"
            return _FakeResponse()

    result = fetch_release_check(
        "https://example.invalid/releases/latest",
        current_version="1.0.0",
        requests_module=_FakeRequests(),
    )
    assert result.has_update is True
    assert result.new_version == "v2.0.0"
    assert result.body == "changes"

    same_result = fetch_release_check(
        "https://example.invalid/releases/latest",
        current_version="2.0.0",
        requests_module=_FakeRequests(),
    )
    assert same_result.has_update is False

    class _MissingNameResponse:
        text = json.dumps({"body": "broken metadata"})

    class _MissingNameRequests:
        def get(self, url):
            return _MissingNameResponse()

    try:
        fetch_release_check(
            "https://example.invalid/releases/latest",
            current_version="1.0.0",
            requests_module=_MissingNameRequests(),
        )
    except UpdateFetchError as exc:
        assert str(exc) == "Release response does not contain a version name"
        assert "broken metadata" in exc.raw_text
    else:
        raise AssertionError("missing release name should raise UpdateFetchError")

    selection = select_release_asset(
        "v2.0.0",
        result.assets,
        system_name="Linux",
        machine_name="x86_64",
    )
    assert selection.found is True
    assert selection.package_name == "v2.0.0-linux.zip"
    assert selection.download_url == "https://example.invalid/linux.zip"
    assert selection.size == 42
    assert selection.download_count == 7

    unsupported = select_release_asset(
        "v2.0.0",
        result.assets,
        system_name="Linux",
        machine_name="arm64",
    )
    assert unsupported.found is False
    assert unsupported.package_name == "v2.0.0-linux.zip"


def _exercise_update_install_service() -> None:
    terminated = []
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        cwd = root / "app"
        temp = root / "temp"
        cwd.mkdir()
        temp.mkdir()
        tool_self = root / "tool-self.exe"
        tool_self.write_bytes(b"self-tool")
        update_zip = root / "update.zip"
        with zipfile.ZipFile(update_zip, "w") as zf:
            zf.writestr("docs/readme.txt", "updated docs")
            zf.writestr("tool.exe", b"new-tool")

        payload = prepare_update_payload(
            str(update_zip),
            cwd_path=str(cwd),
            temp_path=str(temp),
            tool_self_path=str(tool_self),
            open_pids=["123"],
            language="Russian",
            oobe="false",
            version="1.0.0",
            os_name="nt",
            current_pid=456,
            terminate_process_func=lambda pid: terminated.append(pid),
        )
        assert terminated == [123]
        assert (cwd / "docs" / "readme.txt").read_text(
            encoding="utf-8"
        ) == "updated docs"
        assert (cwd / "bin" / "tool.exe").read_bytes() == b"new-tool"
        assert Path(payload.updater_path).name == "updater.exe"
        assert Path(payload.updater_path).read_bytes() == b"self-tool"
        assert payload.update_dict["updating"] == "true"
        assert payload.update_dict["wait_pids"] == "123 456"
        assert payload.update_dict["new_tool"].endswith(os.path.join("bin", "tool.exe"))

        staged = temp / "late" / "file.txt"
        staged.parent.mkdir(parents=True)
        staged.write_text("late update", encoding="utf-8")
        new_tool = cwd / "bin" / "tool.exe"
        applied = apply_staged_update(
            cwd_path=str(cwd),
            temp_path=str(temp),
            new_tool=str(new_tool),
            wait_pids="789",
            update_files="late/file.txt missing.txt",
            version_old="1.0.0",
            os_name="nt",
            current_pid=999,
            terminate_process_func=lambda pid: terminated.append(pid),
        )
        assert applied.success is True
        assert applied.settings_updates == {"wait_pids": "999", "update_done": "true"}
        assert Path(applied.launch_path).name == "tool.exe"
        assert (cwd / "late" / "file.txt").read_text(encoding="utf-8") == "late update"
        assert any(path.endswith("missing.txt") for path in applied.warning_paths)
        assert terminated == [123, 789]

        failed = apply_staged_update(
            cwd_path=str(cwd),
            temp_path=str(temp),
            new_tool=str(root / "missing-tool.exe"),
            wait_pids="",
            update_files="",
            version_old="1.0.0",
            os_name="nt",
            current_pid=1,
            terminate_process_func=lambda pid: terminated.append(pid),
        )
        assert failed.success is False
        assert failed.settings_updates == {"version": "1.0.0", "updating": "false"}

        updater_path = Path(build_updater_path(str(cwd)))
        updater_path.write_bytes(b"helper")
        new_tool.write_bytes(b"to-clean")
        cleanup = cleanup_completed_update(
            updater_path=str(updater_path),
            new_tool=str(new_tool),
            wait_pids="321",
            terminate_process_func=lambda pid: terminated.append(pid),
        )
        assert str(updater_path) in cleanup.removed_paths
        assert str(new_tool) in cleanup.removed_paths
        assert cleanup.failed_paths == ()
        assert terminated[-1] == 321

        unsafe_zip = root / "unsafe.zip"
        with zipfile.ZipFile(unsafe_zip, "w") as zf:
            zf.writestr("../escape.txt", "bad")
        try:
            prepare_update_payload(
                str(unsafe_zip),
                cwd_path=str(cwd),
                temp_path=str(temp),
                tool_self_path=str(tool_self),
                open_pids=[],
                language="Russian",
                oobe="false",
                version="1.0.0",
                os_name="nt",
                current_pid=2,
                terminate_process_func=lambda pid: terminated.append(pid),
            )
        except ValueError as exc:
            assert "Unsafe update archive member" in str(exc)
        else:
            raise AssertionError("unsafe update zip path traversal should be rejected")


def _exercise_update_app_facade_boundary() -> None:
    app_source = Path("src/app/update.py").read_text(encoding="utf-8")
    composition_source = Path("src/app/composition/update.py").read_text(
        encoding="utf-8"
    )
    window_source = Path("src/ui/update/window.py").read_text(encoding="utf-8")

    assert "tkinter" not in app_source
    assert "ttk." not in app_source
    assert "from src.app.composition.update import open_update_window" in app_source
    assert "from src.ui.update.window import UpdaterWindow" in composition_source
    assert "UpdateWorkflowController(" in composition_source
    assert "UpdatePresentationController(" in composition_source
    assert "UpdateOrchestrator(" in composition_source
    assert "UpdateOrchestrator" not in window_source
    assert "fetch_release" not in window_source
    assert "subprocess" not in window_source
    assert "import_module(" not in app_source


def _exercise_updater_hotspots() -> None:
    notice_calls = []

    class _View:
        def winfo_exists(self):
            return True

        def set_notice(self, text, *, color=""):
            notice_calls.append((text, color))

        def append_change_log(self, _text):
            pass

        def set_action_button(self, *, text):
            self.button_text = text

    release = type(
        "Release",
        (),
        {
            "has_update": True,
            "new_version": "v2.0.0",
            "body": "changes",
            "assets": [
                {
                    "name": "v2.0.0-linux.zip",
                    "browser_download_url": "https://example.invalid/linux.zip",
                    "size": 42,
                    "download_count": 11,
                },
            ],
        },
    )()
    workflow = UpdateWorkflowController(
        settings=SimpleNamespace(
            update_done="false", version_old="", set_value=lambda *_: None
        ),
        states=SimpleNamespace(run_source=False),
        orchestrator=SimpleNamespace(),
        task_runner=SimpleNamespace(),
        dispatcher=SimpleNamespace(),
        update_url="https://example.invalid/releases/latest",
        fetch_release=lambda _url: release,
        system_name=lambda: "Linux",
        machine_name=lambda: "x86_64",
    )
    outcome = workflow._check_release()
    assert outcome.selection.found is True
    assert outcome.selection.download_url == "https://example.invalid/linux.zip"
    assert outcome.selection.size == 42
    assert outcome.selection.download_count == 11

    texts = LangUtils()
    texts.load_map(
        {
            "update_presenter_new_version_format": "new %s",
            "update_presenter_update_now": "install",
        }
    )
    view = _View()
    presentation = UpdatePresentationController(
        view=view,
        host_window=SimpleNamespace(),
        settings=SimpleNamespace(),
        states=SimpleNamespace(update_window=True),
        workflow=workflow,
        texts=texts,
    )
    presentation._apply_release_check(outcome)
    assert notice_calls == [("new v2.0.0", "orange")]
    assert view.button_text == "install"

    assert detect_pending_update_mode("tool.exe", "true") is PendingUpdateMode.CLEANUP
    assert detect_pending_update_mode("updater.exe", "false") is PendingUpdateMode.APPLY
    assert (
        detect_pending_update_mode("launcher.py", "false") is PendingUpdateMode.PREPARE
    )

    class _Settings:
        language = "Russian"
        oobe = "false"
        version = "1.0.0"
        version_old = "0.9.0"
        new_tool = ""
        wait_pids = ""
        update_files = ""
        update_done = "false"

        def __init__(self):
            self.values = {}

        def set_value(self, name, value):
            self.values[name] = str(value)
            setattr(self, name, str(value))

    progress = []
    launches = []
    pulls = []
    settings = _Settings()
    states = SimpleNamespace(open_pids=[])
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        temp = root / "temp"
        temp.mkdir()
        orchestrator = UpdateOrchestrator(
            settings=settings,
            states=states,
            cwd_path=str(root),
            temp_path=str(temp),
            tool_self_path=str(root / "tool.exe"),
            downloader=lambda *_args, **_kwargs: [
                (10, 1, 1, 10, 0.1),
                (100, 1, 10, 10, 1.0),
            ],
            process_launcher=lambda command: launches.append(command),
            repository_puller=lambda path: pulls.append(path),
        )
        payload = PreparedUpdatePayload(
            update_dict={"updating": "true"}, updater_path=str(root / "updater.exe")
        )
        orchestrator.prepare_payload = lambda update_zip: payload
        result = orchestrator.download_and_prepare(
            "https://example.invalid/update.zip",
            10,
            on_progress=progress.append,
            is_cancelled=lambda: False,
        )
        assert result is payload
        assert progress == [10, 100, 100]

        orchestrator.persist_and_launch_updater(payload)
        assert settings.values["updating"] == "true"
        assert launches == [str(root / "updater.exe")]

        orchestrator.pull_source_repository()
        assert pulls == [str(root)]


def run_all() -> None:
    _exercise_update_logic_boundary()
    _exercise_update_install_service()
    _exercise_update_app_facade_boundary()
    _exercise_updater_hotspots()


def test_contracts() -> None:
    run_all()

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
