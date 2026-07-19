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

import pytest

from src.app.settings.actions import SettingsService
from src.app.settings.presentation_controller import SettingsPresentationController


class _Settings:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def set_value(self, key: str, value: object) -> None:
        self.values[key] = str(value)
        setattr(self, key, str(value))


class _Var:
    def __init__(self, value: str) -> None:
        self.value = value

    def get(self) -> str:
        return self.value


class _Notifier:
    def __init__(self) -> None:
        self.calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def show(self, *args: object, **kwargs: object) -> None:
        self.calls.append((args, kwargs))


def test_settings_service_validates_all_interactive_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _Settings()
    service = SettingsService(settings=settings, states=SimpleNamespace(in_oobe=False))

    service.set_theme("dark")
    service.set_work_path("/tmp/work")
    service.set_auto_update(True)
    for key in (
        "error_helper_enabled",
        "magisk_not_decompress",
        "boot_skip_ramdisk",
        "auto_unpack",
        "treff",
    ):
        assert service.set_toggle(key, "1") == "1"

    assert settings.values["theme"] == "dark"
    assert settings.values["path"] == "/tmp/work"
    assert settings.values["check_upgrade"] == "1"

    with pytest.raises(ValueError):
        service.set_theme("blue")
    with pytest.raises(ValueError):
        service.set_toggle("unknown", "1")
    with pytest.raises(ValueError):
        service.set_toggle("treff", "yes")


def test_settings_presentation_controller_executes_every_action(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _Settings()
    service = SettingsService(settings=settings, states=SimpleNamespace(in_oobe=True))
    errors: list[tuple[str, Exception]] = []
    calls: list[tuple[str, object]] = []

    controller = SettingsPresentationController(
        service=service,
        read_theme=_Var("light").get,
        read_language=_Var("English").get,
        report_error=lambda context, exc: errors.append((context, exc)),
        apply_theme_appearance=lambda value: calls.append(("theme", value)),
        apply_transparency_appearance=lambda value: calls.append(
            ("transparency", value)
        ),
        confirm_restart_language_change=lambda: False,
        choose_work_path=lambda: "/tmp/new-work",
        apply_work_path_to_view=lambda value: calls.append(("path_view", value)),
        restart_app=lambda: calls.append(("restart", None)),
        launch_updater=lambda: calls.append(("updater", None)),
    )

    monkeypatch.setattr(
        "src.app.settings.actions.apply_language",
        lambda target, value: target.set_value("language", value),
    )

    controller.apply_theme()
    controller.apply_toggle("error_helper_enabled", "1")
    controller.apply_error_helper_confidence("85")
    controller.apply_transparency("1")
    controller.apply_auto_update("1")
    controller.apply_language()
    controller.choose_and_apply_work_path()
    controller.open_updater()

    assert settings.values["theme"] == "light"
    assert settings.values["error_helper_enabled"] == "1"
    assert settings.values["error_helper_confidence"] == "85"
    assert settings.values["treff"] == "1"
    assert settings.values["check_upgrade"] == "1"
    assert settings.values["language"] == "English"
    assert settings.values["path"] == "/tmp/new-work"
    assert ("theme", "light") in calls
    assert ("transparency", True) in calls
    assert ("path_view", "/tmp/new-work") in calls
    assert ("updater", None) in calls
    assert not errors

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
