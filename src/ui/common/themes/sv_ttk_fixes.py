# Workaround ugly font fallbacks on Windows.
# Only for Windows!!
#
# Copyright (C) 2022-2025 The MIO-KITCHEN-SOURCE Project
#
# Licensed under theGNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.gnu.org/licenses/agpl-3.0.en.html#license-text
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations

from collections.abc import Sequence
import tkinter as tk
import tkinter.font as tkfont
from tkinter import Label as OriginalLabel
from tkinter import ttk

_SV_TTK_FONT_NAMES = [
    'SunValleyCaptionFont',
    'SunValleyBodyFont',
    'SunValleyBodyStrongFont',
    'SunValleyBodyLargeFont',
    'SunValleySubtitleFont',
    'SunValleyTitleFont',
    'SunValleyTitleLargeFont',
    'SunValleyDisplayFont',
]


def _tk_get_font(name: str = 'TkDefaultFont') -> tkfont.Font:
    return tkfont.nametofont(name)


def _tk_get_font_family(font: tkfont.Font | None = None) -> str:
    resolved = font if font is not None else _tk_get_font()
    return str(resolved.actual('family'))


def _normalize_label_font(font_spec: object | None) -> object:
    default_family = _tk_get_font_family()
    if font_spec is None:
        return (default_family,)
    if isinstance(font_spec, tkfont.Font):
        font_spec.configure(family=default_family)
        return font_spec
    if isinstance(font_spec, str):
        try:
            named_font = _tk_get_font(font_spec)
        except tk.TclError:
            return (default_family,)
        named_font.configure(family=default_family)
        return named_font
    if isinstance(font_spec, Sequence) and not isinstance(font_spec, (str, bytes)):
        values = tuple(font_spec)
        return (default_family, *values[1:]) if values else (default_family,)
    return (default_family,)


def _label_init_wrapper(original_init, *args: object, **kwargs: object) -> object:
    kwargs['font'] = _normalize_label_font(kwargs.get('font'))
    return original_init(*args, **kwargs)


def _do_hook_label_init() -> None:
    original_init = ttk.Label.__init__
    ttk.Label.__init__ = lambda *args, **kwargs: _label_init_wrapper(original_init, *args, **kwargs)


def do_set_window_deffont(root: tk.Misc) -> None:
    root.option_add('*Font', _tk_get_font())


def do_override_sv_ttk_fonts() -> None:
    family = _tk_get_font_family()
    for font_name in _SV_TTK_FONT_NAMES:
        _tk_get_font(font_name).configure(family=family)


class Label(OriginalLabel):
    def __init__(self, *args: object, **kwargs: object) -> None:
        _label_init_wrapper(OriginalLabel.__init__, self, *args, **kwargs)


_do_hook_label_init()
