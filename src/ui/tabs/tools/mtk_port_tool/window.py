from __future__ import annotations

from tkinter import BOTH

from src.ui.common.windowing import Toplevel
from src.ui.tabs.tools.mtk_port_tool import keys
from src.ui.tabs.tools.mtk_port_tool.panel import MtkPortPanel


class MtkPortTool(Toplevel):
    def __init__(
        self,
        *,
        texts,
        controller,
        initial_directory: str,
        default_boot_image: str = "",
        default_system_image: str = "",
    ) -> None:
        super().__init__()
        self.title(texts.resolve_required_ui_text(keys.TITLE))
        panel = MtkPortPanel(
            self,
            texts=texts,
            controller=controller,
            initial_directory=initial_directory,
            default_boot_image=default_boot_image,
            default_system_image=default_system_image,
        )
        panel.pack(side="top", fill=BOTH, expand=True)
        self.center_on_screen(force=True)


__all__ = ["MtkPortTool"]
