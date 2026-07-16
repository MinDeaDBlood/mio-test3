from __future__ import annotations


from src.app.runtime.contexts.settings import resolve_settings
from src.app.runtime.contexts.ui import resolve_ui_host_window
from src.app.ui_feedback import build_ui_dispatcher
from src.app.ui_tasks import build_ui_task_runner
from src.app.tools.download_firmware_controller import FirmwareDownloadController
from src.app.composition.project_import import build_project_import_controller
from src.app.localization_runtime import lang
from src.logic.tools.download_firmware.use_case import DownloadFirmwareUseCase
from src.core.url_paths import download_filename
from src.ui.common.controls import input_
from src.ui.tabs.tools.download_firmware.view import FirmwareDownloadView


def open_firmware_download(
    *, use_case: DownloadFirmwareUseCase | None = None
) -> object | None:
    settings = resolve_settings()
    host_window = resolve_ui_host_window()
    view = FirmwareDownloadView(host_window=host_window, texts=lang)
    url = view.ask_url(input_)
    if not url:
        view.show_validation_error(view.empty_url_message())
        return None
    dispatcher = build_ui_dispatcher(host_window=host_window)
    controller = FirmwareDownloadController(
        output_dir=settings.path,
        use_case=use_case
        or DownloadFirmwareUseCase(
            importer=build_project_import_controller().import_file
        ),
        dispatcher=dispatcher,
        task_runner=build_ui_task_runner(
            dispatcher=dispatcher, is_alive=host_window.winfo_exists
        ),
    )
    filename = download_filename(url)
    view.open(url, display_name=filename)

    def finish_success(result) -> None:
        view.close()
        view.show_success(filename=filename, elapsed=result.elapsed)

    def finish_error(exc: Exception) -> None:
        view.close()
        view.show_error(str(exc))

    return controller.start(
        url,
        auto_import=view.auto_import_requested,
        on_progress=view.update_progress,
        on_success=finish_success,
        on_error=finish_error,
    )


__all__ = ["open_firmware_download"]
