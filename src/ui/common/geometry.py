from __future__ import annotations

from typing import Protocol


class CenterableWindowProtocol(Protocol):
    def update_idletasks(self) -> object: ...
    def winfo_width(self) -> int: ...
    def winfo_reqwidth(self) -> int: ...
    def winfo_height(self) -> int: ...
    def winfo_reqheight(self) -> int: ...
    def winfo_screenwidth(self) -> int: ...
    def winfo_screenheight(self) -> int: ...
    def geometry(self, geometry: str) -> object: ...


def move_center(master: CenterableWindowProtocol) -> None:
    """Center a Tk or Toplevel window after its geometry has settled."""
    master.update_idletasks()
    width = max(master.winfo_width(), master.winfo_reqwidth())
    height = max(master.winfo_height(), master.winfo_reqheight())
    screen_width = master.winfo_screenwidth()
    screen_height = master.winfo_screenheight()
    x = max(int(screen_width / 2 - width / 2), 0)
    y = max(int(screen_height / 2 - height / 2), 0)
    master.geometry(f'+{x}+{y}')
    master.update_idletasks()


__all__ = ['CenterableWindowProtocol', 'move_center']
