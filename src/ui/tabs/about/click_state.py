from __future__ import annotations

from dataclasses import dataclass
from random import randrange


@dataclass
class AboutTabClickState:
    debugger_clicks: int = 0

    def next_color_and_debug(self, debugger_open: bool) -> tuple[str, bool]:
        self.debugger_clicks += 1
        should_open = self.debugger_clicks >= 5 and not debugger_open
        if should_open:
            self.debugger_clicks = 0
        return self.random_color(), should_open

    @staticmethod
    def random_color() -> str:
        parts = []
        for _ in range(3):
            parts.append(f'{randrange(16, 256):02x}')
        return '#' + ''.join(parts)


__all__ = ['AboutTabClickState']
