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

from src.ui.tabs.tools.download_firmware import keys as download_keys
from src.ui.tabs.tools.download_firmware.view import FirmwareDownloadView
from src.ui.tabs.tools.merge_qualcomm_image import keys as qualcomm_keys
from src.ui.tabs.tools.merge_qualcomm_image.window import MergeQualcommImageWindow


class FakeCatalog:
    def __init__(self, values: dict[str, str]) -> None:
        self.values = values

    def resolve_required_ui_text(self, key: str) -> str:
        return self.values[key]


def test_firmware_download_url_dialog_receives_localization_catalog() -> None:
    texts = FakeCatalog({download_keys.URL_DIALOG_TITLE: "Firmware URL"})
    host = object()
    view = FirmwareDownloadView.__new__(FirmwareDownloadView)
    view.host_window = host
    view.texts = texts
    captured: dict[str, object] = {}

    def input_func(*, texts, title, master, text=""):
        captured.update(texts=texts, title=title, master=master, text=text)
        return "https://example.invalid/firmware.zip"

    result = view.ask_url(input_func)

    assert result == "https://example.invalid/firmware.zip"
    assert captured == {
        "texts": texts,
        "title": "Firmware URL",
        "master": host,
        "text": "",
    }


def test_firmware_download_success_is_presented_in_ui_not_printed() -> None:
    calls: list[tuple[str, str]] = []
    host = SimpleNamespace(message_pop=lambda text, color: calls.append((text, color)))
    view = FirmwareDownloadView.__new__(FirmwareDownloadView)
    view.host_window = host
    view.texts = FakeCatalog(
        {download_keys.COMPLETE_MESSAGE_FORMAT: "Downloaded {0} in {1}s"}
    )

    view.show_success(filename="firmware.zip", elapsed=1.25)

    assert calls == [("Downloaded firmware.zip in 1.25s", "green")]


def test_merge_qualcomm_build_ui_uses_injected_controls(monkeypatch) -> None:
    calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    class Controls:
        def filechose(self, *args, **kwargs):
            calls.append(("filechose", args, kwargs))

        def combobox(self, *args, **kwargs):
            calls.append(("combobox", args, kwargs))

    class Button:
        def __init__(self, *args, **kwargs):
            calls.append(("button", args, kwargs))

        def pack(self, **kwargs):
            calls.append(("pack", (), kwargs))

    texts = FakeCatalog(
        {
            qualcomm_keys.RAWPROGRAM_LABEL: "RawProgram XML:",
            qualcomm_keys.RAWPROGRAM_BROWSE_BUTTON: "Browse rawprogram",
            qualcomm_keys.PARTITION_LABEL: "Partition",
            qualcomm_keys.OUTPUT_DIRECTORY_LABEL: "Output",
            qualcomm_keys.OUTPUT_DIRECTORY_BROWSE_BUTTON: "Browse output",
            qualcomm_keys.RUN_BUTTON: "Run",
        }
    )
    window = MergeQualcommImageWindow.__new__(MergeQualcommImageWindow)
    window._controls = Controls()
    window._language = texts
    window.rawprogram_xml = object()
    window.partition_name = object()
    window.output_path = object()
    window.run = lambda: None
    monkeypatch.setattr(
        "src.ui.tabs.tools.merge_qualcomm_image.window.ttk.Button",
        Button,
    )

    window._build_ui()

    assert [name for name, _args, _kwargs in calls] == [
        "filechose",
        "combobox",
        "filechose",
        "button",
        "pack",
    ]
    assert calls[0][2] == {"browse_text": "Browse rawprogram"}
    assert calls[2][2] == {
        "is_folder": True,
        "browse_text": "Browse output",
    }


def test_merge_qualcomm_composition_attaches_supported_controller(monkeypatch) -> None:
    from src.app.composition import merge_qualcomm_image as composition

    attached: dict[str, object] = {}

    class Window:
        def __init__(self, *, language, controls) -> None:
            attached["language"] = language
            attached["controls"] = controls

        def attach(self, *, controller) -> None:
            attached["controller"] = controller

    monkeypatch.setattr(composition, "MergeQualcommImageWindow", Window)
    monkeypatch.setattr(
        composition,
        "CustomControls",
        lambda **kwargs: SimpleNamespace(**kwargs),
    )
    task_runner = object()
    monkeypatch.setattr(
        composition,
        "build_window_task_runtime",
        lambda window, logger: (object(), task_runner),
    )

    window = composition.open_merge_qualcomm_image_window()

    assert isinstance(window, Window)
    assert attached["controller"]._task_runner is task_runner


def test_merge_qualcomm_error_callback_uses_window_language(monkeypatch) -> None:
    texts = FakeCatalog(
        {
            qualcomm_keys.WARNING_DIALOG_TITLE: "Qualcomm warning",
            qualcomm_keys.WARNING_DIALOG_OK_BUTTON: "Close warning",
        }
    )
    shown: dict[str, object] = {}
    window = MergeQualcommImageWindow.__new__(MergeQualcommImageWindow)
    window._language = texts
    window.winfo_exists = lambda: True
    monkeypatch.setattr(
        "src.ui.tabs.tools.merge_qualcomm_image.window.warn_win",
        lambda *, texts, text, title, ok: shown.update(
            texts=texts,
            text=text,
            title=title,
            ok=ok,
        ),
    )
    monkeypatch.setattr(
        "src.ui.tabs.tools.merge_qualcomm_image.window.logging.error",
        lambda *args, **kwargs: None,
    )

    window._handle_error(RuntimeError("merge failed"))

    assert shown == {
        "texts": texts,
        "text": "merge failed",
        "title": "Qualcomm warning",
        "ok": "Close warning",
    }


def test_mtk_port_composition_injects_controller_before_window_build(
    monkeypatch,
) -> None:
    from src.app.composition import mtk_port_tool as composition

    captured: dict[str, object] = {}
    host_window = object()
    controller = object()

    class Window:
        def __init__(self, **kwargs) -> None:
            captured["window_kwargs"] = kwargs

        def winfo_exists(self) -> bool:
            return True

    class Binaries:
        @staticmethod
        def from_tool_bin(value):
            captured["tool_bin"] = value
            return object()

    monkeypatch.setattr(composition, "resolve_ui_host_window", lambda: host_window)
    monkeypatch.setattr(
        composition,
        "detect_mtk_port_source_defaults",
        lambda: SimpleNamespace(boot_image="boot.img", system_image="system.img"),
    )
    dispatcher = object()

    def build_dispatcher(*, host_window):
        captured["host_window"] = host_window
        return dispatcher

    monkeypatch.setattr(composition, "build_ui_dispatcher", build_dispatcher)

    def build_runner(*, dispatcher, is_alive, logger):
        captured["dispatcher"] = dispatcher
        captured["is_alive"] = is_alive
        captured["logger"] = logger
        return object()

    monkeypatch.setattr(composition, "build_ui_task_runner", build_runner)
    monkeypatch.setattr(composition, "MtkPortBinaries", Binaries)
    profiles = {"profile": {"flags": {}}}
    monkeypatch.setattr(
        composition,
        "load_or_create_mtk_port_profiles",
        lambda: profiles,
    )
    monkeypatch.setattr(
        composition, "build_ui_service_output", lambda *, texts: object()
    )
    monkeypatch.setattr(
        composition, "MtkPortService", lambda **kwargs: SimpleNamespace(**kwargs)
    )
    def build_controller(*, service, task_runner):
        captured["controller_args"] = (service, task_runner)
        return controller

    monkeypatch.setattr(composition, "MtkPortController", build_controller)
    monkeypatch.setattr(composition, "MtkPortTool", Window)

    window = composition.open_mtk_port_tool_window()

    assert isinstance(window, Window)
    assert captured["host_window"] is host_window
    assert captured["window_kwargs"]["controller"] is controller
    assert captured["window_kwargs"]["default_boot_image"] == "boot.img"
    assert captured["window_kwargs"]["default_system_image"] == "system.img"
    assert captured["is_alive"]() is True

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
