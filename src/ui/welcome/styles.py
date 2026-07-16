from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import font as tkfont


CONTENT_PAD_X = 10
CONTENT_PAD_Y = 10
SECTION_GAP = 10
NAVIGATION_PAD = 14
NAVIGATION_GAP = 8
TEXT_INSET = 8


@dataclass(frozen=True)
class WelcomeFonts:
    hero: tkfont.Font
    title: tkfont.Font
    body: tkfont.Font
    note: tkfont.Font


def create_welcome_fonts(master: tk.Misc) -> WelcomeFonts:
    default_font = tkfont.nametofont('TkDefaultFont')
    family = str(default_font.actual('family'))
    return WelcomeFonts(
        hero=tkfont.Font(root=master, family=family, size=36),
        title=tkfont.Font(root=master, family=family, size=24),
        body=tkfont.Font(root=master, family=family, size=18),
        note=tkfont.Font(root=master, family=family, size=11),
    )


__all__ = [
    'CONTENT_PAD_X',
    'CONTENT_PAD_Y',
    'NAVIGATION_GAP',
    'NAVIGATION_PAD',
    'SECTION_GAP',
    'TEXT_INSET',
    'WelcomeFonts',
    'create_welcome_fonts',
]
