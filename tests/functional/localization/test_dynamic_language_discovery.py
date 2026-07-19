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


import json
from functools import partial
from pathlib import Path
from types import SimpleNamespace

from src.app.settings.tab_controller import SettingsTabController
from src.app.welcome.controller import WelcomeContentAccess, WelcomeController
from src.logic.welcome.steps import WelcomeStepPolicy
from src.platform.language_repository import list_language_names
from src.platform.settings_repository import SettingsRepository
from src.platform.welcome_content_repository import WelcomeContentRepository


def _write_language(directory: Path, name: str, text: str) -> None:
    (directory / f"{name}.json").write_text(
        json.dumps({"dynamic_language_probe": text}, ensure_ascii=False),
        encoding="utf-8",
    )


def test_language_files_are_discovered_dynamically_by_settings_and_welcome(
    tmp_path: Path,
) -> None:
    language_dir = tmp_path / "languages"
    license_dir = tmp_path / "licenses"
    language_dir.mkdir()
    license_dir.mkdir()
    _write_language(language_dir, "English", "English")

    settings = SimpleNamespace(
        path=str(tmp_path),
        language="English",
        theme="dark",
        oobe="0",
        set_value=lambda _name, _value: None,
    )
    settings_controller = SettingsTabController(
        settings_obj=settings,
        temp_path=str(tmp_path / "cache"),
        list_languages=partial(list_language_names, language_dir),
    )
    repository = WelcomeContentRepository(
        language_directory=language_dir,
        license_directory=license_dir,
    )
    welcome_controller = WelcomeController(
        settings=settings,
        content_service=WelcomeContentAccess(
            list_languages=repository.list_languages,
            list_licenses=repository.list_licenses,
            read_license=repository.read_license,
            read_private_notice=repository.read_private_notice,
        ),
        current_language=lambda: settings.language,
        frame_count=6,
    )

    assert settings_controller.list_available_languages() == ("English",)
    assert welcome_controller.main_data().languages == ("English",)
    assert welcome_controller.main_data().selected_language == "English"

    _write_language(language_dir, "Esperanto-Community", "Esperanto")

    expected = ("English", "Esperanto-Community")
    assert settings_controller.list_available_languages() == expected
    assert welcome_controller.main_data().languages == expected


def test_bundled_language_setting_names_a_real_language_file() -> None:
    settings = SettingsRepository(set_ini=str(Path("config") / "settings.ini"))
    available = list_language_names(Path("languages"))

    assert settings.language in available
    assert (Path("languages") / f"{settings.language}.json").is_file()
    stored_step = int(settings.oobe)
    assert WelcomeStepPolicy(frame_count=6).clamp(stored_step) == stored_step

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
