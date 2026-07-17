import logging
import os
import sys
from io import BytesIO
from timeit import default_timer as dti

from src.app.runtime.contract import BOOTSTRAP_UI_KEYS, validate_runtime_keys
from src.app.pro_runtime import is_pro, verify
from src.app.runtime.core_access import require_settings
from src.app.runtime.defaults_access import (
    get_tool_log,
    require_log_dir,
    require_states,
)
from src.app.runtime.window_access import require_animation
from src.app.process_lifecycle import exit_tool, restart as _restart_process
from src.app.startup_checks import collect_startup_issues
from src.app.std_streams import ensure_process_streams_installed
from src.app.startup_metrics import StartupTimeline
from src.platform import logging_setup
from src.platform.runtime_directories import ensure_runtime_directories, prepare_log_files
from src.platform.crash_logging import (
    install_tk_exception_logging,
    log_startup_phase,
    start_startup_watchdog,
    stop_startup_watchdog,
)

logger = logging.getLogger(__name__)

start = dti()


_LOG_FORMAT = logging_setup.LOG_FORMAT
_MIO_FILE_HANDLER_ATTR = logging_setup.MIO_FILE_HANDLER_ATTR
_MIO_FILE_HANDLER_PATH_ATTR = logging_setup.MIO_FILE_HANDLER_PATH_ATTR


def _configure_logging() -> None:
    logging_setup.configure_logging(
        development=require_states().development,
        log_path=get_tool_log(),
    )


def _suppress_pillow_debug_noise() -> None:
    logging_setup.suppress_pillow_debug_noise()


def _install_runtime_audit() -> None:
    from src.platform.filesystem_audit import install_filesystem_audit
    from src.platform.runtime_paths import CONFIG_DIR, LOG_DIR, PLUGINS_DIR, TEMP_DIR

    install_filesystem_audit(
        roots=(CONFIG_DIR, PLUGINS_DIR, TEMP_DIR),
        excluded_roots=(LOG_DIR,),
    )


def init_verify() -> None:
    from src.app.composition.crash import show_crash
    from src.ui.startup_issue_presenter import present_startup_issues
    from src.app.composition.dialogs import ask_win
    from src.app.localization_runtime import lang

    present_startup_issues(
        collect_startup_issues(require_settings()),
        texts=lang,
        show_fatal=show_crash,
        confirm_warning=ask_win,
    )


def restart(window=None):
    from src.app.localization_runtime import lang
    from src.ui.common.restart_confirmation import confirm_restart_with_active_tasks

    return _restart_process(
        window, confirm_unsaved=lambda: confirm_restart_with_active_tasks(texts=lang)
    )


def _close_startup_splash_for_interaction(startup_splash, *, phase: str):
    if startup_splash is None:
        return None
    startup_splash.close()
    log_startup_phase(phase)
    return None


def _run_startup_modal_interaction(*, name: str, callback) -> None:
    stop_startup_watchdog()
    log_startup_phase(f"{name} opened")
    try:
        callback()
    finally:
        log_startup_phase(f"{name} closed")
        start_startup_watchdog()


def _show_welcome_if_needed(startup_splash):
    if int(require_settings().oobe) >= 5:
        return startup_splash

    from src.app.composition.welcome import open_welcome

    startup_splash = _close_startup_splash_for_interaction(
        startup_splash,
        phase="application startup splash closed before welcome wizard",
    )
    _run_startup_modal_interaction(
        name="welcome wizard",
        callback=open_welcome,
    )
    return startup_splash


def _maybe_run_updater(startup_splash):
    if require_settings().updating != "true":
        return startup_splash
    from src.app.update import open_updater

    updater = open_updater()
    if updater is None:
        return startup_splash

    startup_splash = _close_startup_splash_for_interaction(
        startup_splash,
        phase="application startup splash closed before updater",
    )

    def wait_for_updater() -> None:
        try:
            updater.wait_window()
        except Exception:
            logging.exception("Cannot wait for the updater window")

    _run_startup_modal_interaction(
        name="updater window",
        callback=wait_for_updater,
    )
    return startup_splash


def _finalize_main_window(main_window) -> None:
    from PIL.Image import open as open_img
    from src.ui.assets import images
    from src.ui.common.themes.sv_ttk_fixes import do_override_sv_ttk_fonts

    require_animation().load_gif(
        open_img(BytesIO(getattr(images, f"loading_{main_window.list2.get()}_byte")))
    )
    require_animation().init()
    from src.ui.startup_status import (
        present_basic_mode_notice,
        present_legacy_windows_warning,
        present_startup_duration,
    )

    from src.app.localization_runtime import lang
    from src.app.std_streams import get_stdout_router

    stdout_router = get_stdout_router()

    def emit_startup_line(message: str) -> None:
        stdout_router.write(message.rstrip("\n") + "\n")

    if not is_pro:
        present_basic_mode_notice(texts=lang, emit=emit_startup_line)
    if is_pro and not verify.state:
        from src.app.localization_runtime import lang
        from src.pro.active_ui import Active

        Active(verify, require_settings(), main_window, images, lang).gui()

    main_window.update()
    from src.ui.common.geometry import move_center

    move_center(main_window)
    main_window.loops.append(main_window.get_time)
    if require_settings().check_upgrade == "1":
        from src.app.update import check_upgrade_async

        main_window.loops.append(lambda: check_upgrade_async(main_window))
    present_startup_duration(dti() - start, texts=lang, emit=emit_startup_line)
    if os.name == "nt":
        do_override_sv_ttk_fonts()
        if sys.getwindowsversion().major <= 6:
            present_legacy_windows_warning(texts=lang)


def _schedule_cmdline_parse(main_window, args: list[str]) -> None:
    if not (len(args) > 1 and is_pro):
        return
    from src.app.cmdline import CommandLineProcessor

    main_window.after(1000, CommandLineProcessor, args[1:])


def _init_tk(args: list):
    """Application bootstrap — create the main window and enter mainloop.

    This is an internal function. External callers should use :func:`init`.
    """
    from tkinter import TclError

    timeline = StartupTimeline()
    log_startup_phase('bootstrap entered')
    ensure_process_streams_installed()
    timeline.mark("process_streams")
    ensure_runtime_directories()
    prepare_log_files(require_log_dir(), get_tool_log())
    _configure_logging()
    _install_runtime_audit()
    log_startup_phase('runtime directories, logging and audit ready')

    try:
        from src.app.localization_selection import load_selected_language

        load_selected_language(require_settings())
    except (FileNotFoundError, ValueError) as exc:
        logger.exception('Selected language could not be loaded')
        from src.platform.language_repository import read_language_map
        from src.ui import startup_checks_keys
        from src.ui.startup_checks import present_fatal_startup_error

        reference_texts = read_language_map("English")
        present_fatal_startup_error(
            title=reference_texts.get(
                startup_checks_keys.FATAL_ERROR_DIALOG_TITLE,
                f"[missing:{startup_checks_keys.FATAL_ERROR_DIALOG_TITLE}]",
            ),
            message=str(exc),
        )
    timeline.mark("preload_language")
    from src.app.composition.main_window import create_main_window

    main_window = create_main_window()
    install_tk_exception_logging(main_window)
    from src.ui.startup_splash import show_startup_splash

    startup_splash = show_startup_splash(main_window)
    log_startup_phase('application startup splash ready')
    log_startup_phase('main window created')
    timeline.mark("build_main_window")
    from src.app.composition.window_runtime import initialize_window_runtime

    window_runtime = initialize_window_runtime(main_window)
    timeline.mark("ui_scheduler")

    settings = require_settings()
    try:
        settings.load()
    except (FileNotFoundError, ValueError) as exc:
        from src.app.composition.crash import show_crash

        show_crash(1, str(exc))
    from src.app.runtime.core_access import require_project_manager

    require_project_manager().set_workspace_path(settings.path)
    from src.platform.filesystem_audit import register_audit_root

    register_audit_root(settings.path)
    from src.ui.tabs.settings.appearance.actions import apply_initial_appearance

    effect_alpha = settings.barlevel
    apply_initial_appearance(
        window=main_window,
        theme_var=window_runtime.theme,
        language_var=window_runtime.language,
        theme_name=settings.theme,
        language_name=settings.language,
        transparent_enabled=str(settings.treff) == "1",
        effect_alpha=effect_alpha,
    )
    if is_pro:
        verify.verify(settings.active_code)
    timeline.mark("settings_load")
    startup_splash = _maybe_run_updater(startup_splash)
    timeline.mark("updater_gate")
    startup_splash = _show_welcome_if_needed(startup_splash)
    timeline.mark("welcome_interaction", excluded_from_total=True)
    init_verify()
    timeline.mark("init_verify")
    try:
        main_window.winfo_exists()
    except TclError:
        logging.exception("TclError")
        if startup_splash is not None:
            startup_splash.close()
        stop_startup_watchdog()
        return

    from src.app.composition.main_window import compose_main_window

    composition = compose_main_window(main_window)
    log_startup_phase('main window composition completed')
    timeline.mark("build_gui")
    from src.app.runtime.phases import register_bootstrap_ui_runtime

    register_bootstrap_ui_runtime(
        unpack_view=composition.unpack_view,
        project_menu=composition.project_menu,
    )
    validate_runtime_keys(BOOTSTRAP_UI_KEYS, context="bootstrap ui phase")
    _finalize_main_window(main_window)
    timeline.mark("finalize_main_window")
    if startup_splash is not None:
        startup_splash.close()
    stop_startup_watchdog()
    log_startup_phase('main window revealed')
    require_states().inited = True
    main_window.protocol("WM_DELETE_WINDOW", exit_tool)
    _schedule_cmdline_parse(main_window, args)
    timeline.mark("schedule_cmdline")
    timeline.log(logger=logging)
    try:
        main_window.after(1000, main_window.start_loops)
        log_startup_phase('Tk mainloop entered')
        main_window.mainloop()
        logger.info('Tk mainloop returned normally')
    except KeyboardInterrupt:
        exit_tool()
    return composition


def init(args):
    """Public entry point — initialize and run the application."""
    _init_tk(args)


__all__ = ["init_verify", "exit_tool", "restart", "init"]
