from __future__ import annotations

from src.app.composition._ui_task import build_window_task_runtime
from src.app.composition.dialogs import choose_directory, choose_file
from src.app.localization_runtime import lang
from src.app.tools.decrypt_xtc_xml_controller import DecryptXtcXmlController
from src.ui.common.windowing import CustomControls
from src.ui.tabs.tools.decrypt_xtc_xml import keys
from src.ui.tabs.tools.decrypt_xtc_xml.window import DecryptXtcXml


def open_decrypt_xtc_xml_window() -> DecryptXtcXml:
    window = DecryptXtcXml(
        language=lang,
        controls=CustomControls(
            texts=lang,
            choose_file=choose_file,
            choose_directory=lambda: choose_directory(
                title=lang.resolve_required_ui_text(keys.DIRECTORY_DIALOG_TITLE)
            ),
        ),
    )
    _, task_runner = build_window_task_runtime(window)
    window.attach(controller=DecryptXtcXmlController(task_runner=task_runner))
    return window


__all__ = ["open_decrypt_xtc_xml_window"]
