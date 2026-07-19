from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import font as tkfont


CONTENT_PAD_X = 10
CONTENT_PAD_Y = 10
SECTION_GAP = 10
NAVIGATION_PAD = 5
NAVIGATION_GAP = 5
WORKDIR_WRAP = 200


@dataclass(frozen=True)
class WelcomeFonts:
    hero: tkfont.Font
    title: tkfont.Font
    document_title: tkfont.Font
    body: tkfont.Font
    note: tkfont.Font


def create_welcome_fonts(master: tk.Misc) -> WelcomeFonts:
    default_font = tkfont.nametofont('TkDefaultFont')
    family = str(default_font.actual('family'))
    default_size = int(default_font.actual('size'))
    return WelcomeFonts(
        hero=tkfont.Font(root=master, family=family, size=40),
        title=tkfont.Font(root=master, family=family, size=20),
        document_title=tkfont.Font(root=master, family=family, size=25),
        body=tkfont.Font(root=master, family=family, size=20),
        note=tkfont.Font(root=master, family=family, size=default_size),
    )


__all__ = [
    'CONTENT_PAD_X',
    'CONTENT_PAD_Y',
    'NAVIGATION_GAP',
    'NAVIGATION_PAD',
    'SECTION_GAP',
    'WORKDIR_WRAP',
    'WelcomeFonts',
    'create_welcome_fonts',
]
