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
import logging
import tempfile
from pathlib import Path
from tests.support.source_analysis import top_level_import_modules


def _exercise_toolbox_localization_from_files() -> None:
    import json
    from src.app.localization import ensure_selected_language_loaded
    from src.app.localization_runtime import lang

    ru = json.loads((Path("languages") / "Russian.json").read_text(encoding="utf-8"))
    en = json.loads((Path("languages") / "English.json").read_text(encoding="utf-8"))
    from src.ui.tabs.tools import keys as tool_keys
    from src.ui.tabs.tools.toolbox import _TOOL_SPECS

    toolbox_keys = (
        tool_keys.TITLE,
        *(key for key, _opener_id in _TOOL_SPECS),
    )
    for key in toolbox_keys:
        assert isinstance(ru.get(key), str) and ru.get(key).strip(), key
        assert isinstance(en.get(key), str) and en.get(key).strip(), key

    previous_translations = dict(getattr(lang, "_translations", {}))
    previous_language = lang.current_language()
    previous_language_file = lang.current_language_file()
    try:
        lang.set_source(
            language_name="English",
            language_file=str(Path("languages") / "English.json"),
        )
        lang.load_map({})
        current = ensure_selected_language_loaded(*toolbox_keys, base_path=Path.cwd())
        assert current == "English"
        for key in toolbox_keys:
            assert lang.resolve(key, default="") == en[key]
    finally:
        lang.set_source(
            language_name=previous_language, language_file=previous_language_file
        )
        lang.load_map(previous_translations)


def _exercise_localization_bootstrap() -> None:
    from src.platform.settings_repository import SettingsRepository
    from src.app.localization_runtime import lang
    from src.app.localization_selection import apply_language, load_selected_language

    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        language_dir = root / "languages"
        language_dir.mkdir(parents=True, exist_ok=True)
        (language_dir / "Russian.json").write_text(
            '{"text23": "Обновить", "text134": "Запуск занял : %s Секунд"}',
            encoding="utf-8",
        )
        setting_ini = root / "config" / "settings.ini"
        setting_ini.parent.mkdir(parents=True, exist_ok=True)
        setting_ini.write_text("[setting]\nlanguage = Russian\n", encoding="utf-8")

        workdir = root / "workdir"
        workdir.mkdir()

        from src.platform import settings_repository as settings_module

        old_prog_path = settings_module.prog_path
        try:
            settings_module.prog_path = str(root)
            settings = SettingsRepository(set_ini=str(setting_ini), load=False)
            selected = load_selected_language(settings, base_path=root)
            assert selected == "Russian"
            assert settings.language == "Russian"
            assert lang.resolve_required_ui_text("text23") == "Обновить"
            assert (lang.resolve_required_ui_text("text134") % 1.5).startswith("Запуск занял")

            (language_dir / "German.json").write_text(
                '{"text23": "Aktualisieren"}', encoding="utf-8"
            )
            apply_language(settings, "German", base_path=root)
            assert lang.resolve_required_ui_text("text23") == "Aktualisieren"
            assert lang.resolve_required_ui_text("text134") == "[missing:text134]"
        finally:
            settings_module.prog_path = old_prog_path


def _exercise_localization_logging_contract() -> None:
    from src.app.localization import (
        ensure_selected_language_loaded,
        load_language_from_files,
    )
    from src.app.localization_runtime import lang

    class _Capture(logging.Handler):
        def __init__(self):
            super().__init__()
            self.records = []

        def emit(self, record):
            self.records.append(record)

    previous_translations = dict(getattr(lang, "_translations", {}))
    previous_language = lang.current_language()
    previous_language_file = lang.current_language_file()
    handler = _Capture()
    root_logger = logging.getLogger()
    previous_level = root_logger.level
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    try:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            language_dir = root / "languages"
            language_dir.mkdir(parents=True, exist_ok=True)
            (language_dir / "Russian.json").write_text(
                json.dumps(
                    {
                        "toolbox": "Инструменты",
                        "path": "None",
                        "text23": "Обновить",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            load_language_from_files("Russian", base_path=root)
            assert lang.resolve_required_ui_text("path") == "[missing:path]"
            ensure_selected_language_loaded("toolbox", "path", base_path=root)

        messages = [record.getMessage() for record in handler.records]
        assert any(
            "Loaded language map: language=Russian" in message for message in messages
        )
        assert any(
            "Language map loaded but required keys are still missing/invalid" in message
            and "keys=path" in message
            for message in messages
        )
        assert any(
            "Localization missing key; default='[missing:path]'" in message
            and "context=required" in message
            and "resolution=marker" in message
            and "keys=path" in message
            and "language=Russian" in message
            and "Russian.json" in message
            and (
                "tests/smoke/targeted.py" in message
                or "test_localization_and_settings_contracts.py" in message
            )
            for message in messages
        )
    finally:
        root_logger.removeHandler(handler)
        root_logger.setLevel(previous_level)
        lang.set_source(
            language_name=previous_language, language_file=previous_language_file
        )
        lang.load_map(previous_translations)


def _exercise_localization_resolution_policy() -> None:
    from src.app.localization_runtime import lang

    previous_translations = dict(getattr(lang, "_translations", {}))
    previous_reference_translations = dict(getattr(lang, "_reference_translations", {}))
    previous_language = lang.current_language()
    previous_language_file = lang.current_language_file()
    previous_reference_language = lang.reference_language()
    previous_reference_language_file = lang.reference_language_file()
    try:
        lang.set_source(language_name="Russian", language_file="Russian.json")
        lang.load_map({"ok": "ОК", "empty_label": "", "bad_label": "None"})
        lang.load_reference_map(
            {"missing_button": "Install", "bad_label": "Reference label"},
            language_name="English",
            language_file="English.json",
        )

        assert lang.resolve_optional("missing_button") == ""
        assert lang.resolve("missing_button", default="", context="optional") == ""
        assert lang.resolve_ui_text("missing_button") == "Install"
        assert lang.resolve_required_ui_text("missing_button") == "Install"
        assert lang.resolve_required_ui_text("bad_label") == "Reference label"
        assert (
            lang.resolve_required_ui_text("missing_everywhere")
            == "[missing:missing_everywhere]"
        )
        assert lang.resolve_optional("missing_everywhere") == ""
        assert (
            lang.resolve("missing_everywhere", default="custom", context="optional")
            == "custom"
        )
    finally:
        lang.set_source(
            language_name=previous_language, language_file=previous_language_file
        )
        lang.load_map(previous_translations)
        lang.load_reference_map(
            previous_reference_translations,
            language_name=previous_reference_language,
            language_file=previous_reference_language_file,
        )


def _exercise_settings_manager_runtime_actions() -> None:
    from tkinter import StringVar, Tcl

    from src.app.runtime.flags import States
    from src.platform.settings_repository import SettingsRepository
    from src.app.settings.actions import SettingsService
    from src.app.settings.presentation_controller import SettingsPresentationController

    class _Animation:
        def __init__(self):
            self.calls = []

        def load_gif(self, *_args, **_kwargs):
            self.calls.append(("load_gif", None))

    class _Window:
        def __init__(self, interpreter):
            self.show_local = StringVar(master=interpreter, value="")
            self.list2 = StringVar(master=interpreter, value="dark")

        def attributes(self, *_args, **_kwargs):
            return None

    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        language_dir = root / "languages"
        language_dir.mkdir(parents=True, exist_ok=True)
        (language_dir / "English.json").write_text(
            '{"text129": "Language", "t36": "Restart?"}', encoding="utf-8"
        )
        (language_dir / "German.json").write_text(
            '{"text129": "Sprache", "t36": "Neustart?"}', encoding="utf-8"
        )
        setting_ini = root / "config" / "settings.ini"
        setting_ini.parent.mkdir(parents=True, exist_ok=True)
        setting_ini.write_text(
            "[setting]\nlanguage = English\npath = \n", encoding="utf-8"
        )
        workdir = root / "workdir"
        workdir.mkdir()

        from src.platform import settings_repository as settings_module

        old_prog_path = settings_module.prog_path
        restart_calls = []
        try:
            settings_module.prog_path = str(root)
            settings = SettingsRepository(set_ini=str(setting_ini), load=False)
            interpreter = Tcl()
            window = _Window(interpreter)
            language = StringVar(master=interpreter, value="German")
            service = SettingsService(
                settings=settings,
                states=States(),
            )
            errors = []
            actions = SettingsPresentationController(
                service=service,
                read_theme=window.list2.get,
                read_language=language.get,
                report_error=lambda context, exc: errors.append((context, exc)),
                apply_theme_appearance=lambda _theme: None,
                apply_transparency_appearance=lambda _enabled: None,
                confirm_restart_language_change=lambda: True,
                choose_work_path=lambda: str(workdir),
                apply_work_path_to_view=window.show_local.set,
                restart_app=lambda: restart_calls.append("restart"),
                launch_updater=lambda: None,
            )

            actions.apply_language()
            assert settings.language == "German"
            assert restart_calls == ["restart"]

            actions.choose_and_apply_work_path()
            assert settings.path == str(workdir)
            assert window.show_local.get() == str(workdir)
        finally:
            settings_module.prog_path = old_prog_path


def _exercise_error_helper_unavailable_result() -> None:
    from src.logic.help.error_helper.service import get_error_helper_match

    assert get_error_helper_match("Traceback", rules=None) is None
    assert get_error_helper_match("Traceback", rules=()) is None


def _exercise_error_helper_from_localization_keys() -> None:
    from src.app.localization import read_language_map
    from src.app.help.error_helper.localized_rules import (
        error_helper_detail_key,
        error_helper_solution_key,
        load_error_helper_rules_from_language_map,
    )
    from src.logic.help.error_helper.service import get_error_helper_match

    translations = read_language_map("English", base_path=Path.cwd())
    rules = load_error_helper_rules_from_language_map(translations)
    result = get_error_helper_match(
        "error: ext4_allocate_best_fit_partial: failed to allocate xxx blocks, out of space?",
        threshold=80,
        rules=rules,
    )
    assert result is not None
    assert result.rule_id == "ext4_size_too_small"
    assert (
        error_helper_detail_key(result.rule_id)
        == "error_helper_ext4_size_too_small_detail"
    )
    assert (
        error_helper_solution_key(result.rule_id)
        == "error_helper_ext4_size_too_small_solution"
    )


def _exercise_logic_dialog_boundary_cleanup() -> None:
    import inspect

    assert not Path("src/logic/common/ui_feedback.py").exists()
    assert not Path("src/logic/home/file_dialog_service.py").exists()
    assert not Path("src/app/dialogs.py").exists()
    assert not Path("src/app/runtime/contexts/dialogs.py").exists()

    ui_feedback_imports = top_level_import_modules("src/app/ui_feedback.py")
    assert "src.app.composition.dialogs" not in ui_feedback_imports

    from src.app.composition import dialogs as composition_dialogs
    from src.app.composition.project_import import build_project_import_controller

    original_choose_file = composition_dialogs.choose_file
    original_choose_directory = composition_dialogs.choose_directory
    try:
        composition_dialogs.choose_file = lambda **kwargs: ("file", kwargs)
        composition_dialogs.choose_directory = lambda **kwargs: ("directory", kwargs)
        assert composition_dialogs.choose_file(title="Pick file") == (
            "file",
            {"title": "Pick file"},
        )
        assert composition_dialogs.choose_directory(title="Pick dir") == (
            "directory",
            {"title": "Pick dir"},
        )
    finally:
        composition_dialogs.choose_file = original_choose_file
        composition_dialogs.choose_directory = original_choose_directory

    parameters = inspect.signature(build_project_import_controller).parameters
    assert "confirm_ofp_mtk_decrypt" in parameters


def run_all() -> None:
    _exercise_toolbox_localization_from_files()
    _exercise_localization_bootstrap()
    _exercise_localization_logging_contract()
    _exercise_localization_resolution_policy()
    _exercise_settings_manager_runtime_actions()
    _exercise_error_helper_unavailable_result()
    _exercise_error_helper_from_localization_keys()
    _exercise_logic_dialog_boundary_cleanup()


def test_contracts() -> None:
    run_all()

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
