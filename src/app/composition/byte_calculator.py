from __future__ import annotations

from src.app.localization_runtime import lang
from src.app.tools.byte_calculator_controller import ByteCalculatorController
from src.logic.tools.byte_calculator.service import UNITS
from src.ui.tabs.tools.byte_calculator.window import FileBytes


def open_byte_calculator_window() -> FileBytes:
    return FileBytes(
        language=lang,
        units=UNITS,
        controller=ByteCalculatorController(),
    )


__all__ = ['open_byte_calculator_window']
