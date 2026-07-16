from __future__ import annotations

from src.logic.tools.byte_calculator.service import convert_text


class ByteCalculatorController:
    def __init__(self, *, convert_func=convert_text) -> None:
        self._convert_func = convert_func

    def convert_value(self, text: str, origin_unit: str, target_unit: str) -> str:
        return self._convert_func(text, origin_unit, target_unit)


__all__ = ['ByteCalculatorController']
