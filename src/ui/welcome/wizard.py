from __future__ import annotations

from collections.abc import Callable
import tkinter as tk
from tkinter import BOTH, X, ttk

from src.ui.localization import LocalizationCatalog
from src.ui.welcome.contracts import WelcomeActionsPort, WelcomeControllerPort, WelcomeViewPort
from src.ui.welcome.layout import (
    WelcomePageLayout,
    compute_content_wrap_width,
    fit_welcome_window,
    get_page_layout,
    release_welcome_window,
)
from src.ui.welcome.navigation import get_labels
from src.ui.welcome.navigation_presenter import WelcomeNavigationPresenter
from src.ui.welcome.page_builders import build_done, build_hello, build_license, build_main, build_private, build_set_workdir
from src.ui.common.window_appearance import current_theme_id
from src.ui.common.themes.native_palette import apply_native_theme
from src.ui.common.window_redraw import suspend_window_redraw
from src.ui.welcome.styles import NAVIGATION_GAP, NAVIGATION_PAD, WelcomeFonts, create_welcome_fonts


PageBuilder = Callable[[WelcomeViewPort], None]


class Welcome(ttk.Frame):
    def __init__(
        self,
        *,
        main_window: tk.Tk,
        controller: WelcomeControllerPort,
        language_var: tk.StringVar,
        actions: WelcomeActionsPort,
        texts: LocalizationCatalog,
    ) -> None:
        super().__init__(master=main_window)
        self.main_window = main_window
        self.controller = controller
        self.language_var = language_var
        self.actions = actions
        self.texts = texts
        self.fonts: WelcomeFonts = create_welcome_fonts(main_window)
        self.page_layout: WelcomePageLayout = get_page_layout(0)
        self.content_wrap_width = self.page_layout.preferred_width
        self.frames: dict[int, PageBuilder] = {
            0: build_hello,
            1: build_main,
            2: build_set_workdir,
            3: build_license,
            4: build_private,
            5: build_done,
        }
        if controller.frame_count != len(self.frames):
            raise ValueError(
                f'Welcome controller expects {controller.frame_count} pages, '
                f'but the UI provides {len(self.frames)}.'
            )

        self.actions.set_oobe_active(True)
        self.pack(fill=BOTH, expand=True)
        self.content_host = ttk.Frame(self)
        self.content_host.rowconfigure(0, weight=1)
        self.content_host.columnconfigure(0, weight=1)
        self.content_host.pack(
            expand=True,
            fill=BOTH,
            padx=NAVIGATION_PAD,
            pady=(NAVIGATION_PAD, NAVIGATION_GAP),
        )
        self.frame = ttk.Frame(self.content_host)
        self.frame.grid(row=0, column=0, sticky='nsew')

        self.button_frame = ttk.Frame(self)
        self.button_frame.columnconfigure(0, weight=1, uniform='welcome_navigation')
        self.button_frame.columnconfigure(1, weight=1, uniform='welcome_navigation')
        labels = get_labels(self.texts)
        self.back = ttk.Button(
            self.button_frame,
            text=labels.back,
            command=lambda: self.change_page(self.oobe - 1),
        )
        self.back.grid(row=0, column=0, sticky='ew', padx=(0, NAVIGATION_GAP))
        self.next = ttk.Button(
            self.button_frame,
            text=labels.next,
            command=lambda: self.change_page(self.oobe + 1),
        )
        self.next.grid(row=0, column=1, sticky='ew', padx=(NAVIGATION_GAP, 0))
        self.button_frame.pack(expand=False, fill=X, padx=NAVIGATION_PAD, pady=(0, NAVIGATION_PAD))

        self.oobe = self.controller.initial_step()
        try:
            self.change_page(self.oobe)
            self.main_window.deiconify()
            self.main_window.lift()
            self.main_window.update_idletasks()
            self.wait_window()
        finally:
            self.actions.set_oobe_active(False)

    def _clear_frame(self) -> None:
        for widget in self.frame.winfo_children():
            widget.destroy()

    def _prepare_page_layout(self, step: int) -> None:
        self.page_layout = get_page_layout(step)
        self.content_wrap_width = compute_content_wrap_width(
            screen_width=self.main_window.winfo_screenwidth(),
            layout=self.page_layout,
        )

    def _refresh_window_layout(self) -> None:
        fit_welcome_window(self.main_window, self, layout=self.page_layout)

    def change_page(self, step: int = 0) -> None:
        with suspend_window_redraw(self.main_window):
            self.oobe = self.controller.persist_step(step)
            self._prepare_page_layout(self.oobe)
            self._clear_frame()
            self.frames[self.oobe](self)
            apply_native_theme(self.frame, current_theme_id())

            nav_state = WelcomeNavigationPresenter.build_state(
                step=self.oobe,
                frame_count=len(self.frames),
                labels=get_labels(self.texts),
            )
            self.back.config(
                state='normal' if nav_state.back_enabled else 'disabled'
            )
            if nav_state.is_last:
                self.next.config(
                    text=nav_state.next_text,
                    command=self.destroy_welcome,
                )
            else:
                self.next.config(
                    text=nav_state.next_text,
                    command=lambda: self.change_page(self.oobe + 1),
                )
            self._refresh_window_layout()
            self.next.focus_set()
            self.main_window.update_idletasks()

    def destroy_welcome(self) -> None:
        self.actions.set_oobe_active(False)
        if self.winfo_exists():
            self.destroy()
        release_welcome_window(self.main_window)


__all__ = ['Welcome']
