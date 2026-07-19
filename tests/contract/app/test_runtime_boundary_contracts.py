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


from pathlib import Path

import pytest

from tests.support.source_analysis import top_level_import_modules


def _snapshot_phases():
    from src.app.runtime import phases

    return (
        phases._REGISTERED_EARLY_RUNTIME_DEFAULTS,
        phases._REGISTERED_CORE_RUNTIME_SERVICES,
        phases._REGISTERED_BOOTSTRAP_WINDOW_RUNTIME,
        phases._REGISTERED_BOOTSTRAP_UI_RUNTIME,
    )


def _restore_phases(snapshot) -> None:
    from src.app.runtime import phases

    (
        phases._REGISTERED_EARLY_RUNTIME_DEFAULTS,
        phases._REGISTERED_CORE_RUNTIME_SERVICES,
        phases._REGISTERED_BOOTSTRAP_WINDOW_RUNTIME,
        phases._REGISTERED_BOOTSTRAP_UI_RUNTIME,
    ) = snapshot


def _reset_phases() -> None:
    _restore_phases((None, None, None, None))


def _exercise_explicit_service_bootstrap() -> None:
    from src.app.runtime.service_bootstrap import build_runtime_bootstrap_services

    imports = top_level_import_modules("src/app/runtime/service_bootstrap.py")
    assert not any(
        module == "src.ui" or module.startswith("src.ui.") for module in imports
    )
    assert not any(
        module == "tkinter" or module.startswith("tkinter.") for module in imports
    )

    services = build_runtime_bootstrap_services()
    assert set(services.export_runtime_values()) == {
        "settings",
        "module_error_codes",
        "module_manager",
        "project_manager",
    }
    assert services.project_manager.runtime.workspace_path == services.settings.path
    assert services.project_manager.runtime.current_project_name is None
    assert not hasattr(services, "custom_controls")


def _exercise_typed_phase_registration() -> None:
    from src.app.runtime.core_access import (
        require_module_error_codes,
        require_module_manager,
        require_project_manager,
        require_settings,
    )
    from src.app.runtime.defaults_access import require_log_dir, require_temp_path
    from src.app.runtime.phases import (
        register_bootstrap_ui_runtime,
        register_bootstrap_window_runtime,
        register_core_runtime_services,
        register_early_runtime_defaults,
    )
    from src.app.runtime.window_access import (
        require_animation,
        require_current_project_name,
        require_language,
        require_main_window,
        require_project_menu,
        require_theme,
        require_ui_scheduler,
        require_unpack_view,
    )

    snapshot = _snapshot_phases()
    _reset_phases()
    try:
        settings = object()
        module_errors = object()
        module_manager = object()
        project_manager = object()
        main_window = object()
        animation = object()
        scheduler = object()
        project_name = object()
        theme = object()
        language = object()
        unpack_view = object()
        project_menu = object()

        register_early_runtime_defaults(
            prog_path="/program",
            tool_self="/program/tool.py",
            temp="/program/temp",
            log_dir="/program/logs",
            tool_log="/program/logs/tool.log",
            context_rule_file="/program/context_rules.json",
            states=object(),
            call=object(),
            module_exec="/program/exec.sh",
        )
        register_core_runtime_services(
            settings=settings,
            module_error_codes=module_errors,
            module_manager=module_manager,
            project_manager=project_manager,
        )
        register_bootstrap_window_runtime(
            main_window=main_window,
            animation=animation,
            ui_scheduler=scheduler,
            current_project_name=project_name,
            theme=theme,
            language=language,
        )
        register_bootstrap_ui_runtime(
            unpack_view=unpack_view, project_menu=project_menu
        )

        assert require_temp_path() == "/program/temp"
        assert require_log_dir() == "/program/logs"
        assert require_settings() is settings
        assert require_module_error_codes() is module_errors
        assert require_module_manager() is module_manager
        assert require_project_manager() is project_manager
        assert require_main_window() is main_window
        assert require_animation() is animation
        assert require_ui_scheduler() is scheduler
        assert require_current_project_name() is project_name
        assert require_theme() is theme
        assert require_language() is language
        assert require_unpack_view() is unpack_view
        assert require_project_menu() is project_menu
    finally:
        _restore_phases(snapshot)


def _exercise_missing_values_fail_explicitly() -> None:
    from src.app.runtime.core_access import require_settings
    from src.app.runtime.defaults_access import require_temp_path
    from src.app.runtime.errors import MissingRuntimeValueError
    from src.app.runtime.window_access import require_main_window

    snapshot = _snapshot_phases()
    _reset_phases()
    try:
        for resolver in (require_temp_path, require_settings, require_main_window):
            with pytest.raises(MissingRuntimeValueError):
                resolver()
    finally:
        _restore_phases(snapshot)


def _exercise_runtime_module_boundaries() -> None:
    service_imports = top_level_import_modules("src/app/runtime/service_bootstrap.py")
    phases_imports = top_level_import_modules("src/app/runtime/phases.py")
    defaults_imports = top_level_import_modules("src/app/runtime/defaults.py")

    assert "src.ui.common.windowing" not in service_imports
    assert "src.app.runtime.service_bootstrap" not in phases_imports
    assert "src.app.runtime.models" in phases_imports
    assert "src.app.runtime.phases" not in defaults_imports

    for removed_path in (
        "src/app/runtime_state.py",
        "src/app/runtime_accessors.py",
        "src/app/runtime_compat.py",
        "src/app/tk_runtime.py",
        "src/app/runtime/loader.py",
        "src/app/runtime/registry.py",
        "src/app/runtime/store.py",
    ):
        assert not Path(removed_path).exists(), removed_path


def run_all() -> None:
    _exercise_explicit_service_bootstrap()
    _exercise_typed_phase_registration()
    _exercise_missing_values_fail_explicitly()
    _exercise_runtime_module_boundaries()


def test_contracts() -> None:
    run_all()


def test_project_manager_requires_explicit_project_name_binding(tmp_path):
    from src.app.runtime.models import BootstrapProjectPathRuntime
    from src.logic.projects.common.project_manager import ProjectManager

    class Settings:
        path = str(tmp_path)

    manager = ProjectManager(BootstrapProjectPathRuntime(workspace_path=Settings.path))

    with pytest.raises(RuntimeError, match="current_project_name"):
        manager.current_work_path()

    class ProjectName:
        def __init__(self):
            self.value = "Demo"

        def get(self):
            return self.value

        def set(self, value):
            self.value = value

    project_name = ProjectName()
    manager.bind_current_project_name(project_name)

    assert manager.current_project_name is project_name
    assert Path(manager.current_work_path()) == tmp_path / "Projects" / "Demo" / "unpack"
    assert Path(manager.current_input_path()) == tmp_path / "Projects" / "Demo" / "input"
    assert Path(manager.current_work_output_path()) == tmp_path / "Projects" / "Demo" / "output"


def test_bootstrap_binds_project_name_before_main_ui_initialization():
    bootstrap_source = Path("src/app/bootstrap.py").read_text(encoding="utf-8")
    runtime_source = Path("src/app/composition/window_runtime.py").read_text(
        encoding="utf-8"
    )

    bind_index = runtime_source.index(
        "require_project_manager().bind_current_project_name(current_project_name)"
    )
    register_index = runtime_source.index("register_bootstrap_window_runtime(")
    initialize_index = bootstrap_source.index("initialize_window_runtime(main_window)")
    settings_index = bootstrap_source.index("settings.load()")

    assert bind_index < register_index
    assert initialize_index < settings_index

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
