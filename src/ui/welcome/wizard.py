from __future__ import annotations

from collections.abc import Callable
import tkinter as tk
from tkinter import BOTH, X, TclError, ttk

from src.ui.common.themes.native_palette import apply_native_theme
from src.ui.common.window_appearance import current_theme_id, current_window_alpha
from src.ui.common.window_reveal import reveal_window_after_layout
from src.ui.common.window_transition import snapshot_window_transition
from src.ui.localization import LocalizationCatalog
from src.ui.welcome.contracts import WelcomeActionsPort, WelcomeControllerPort, WelcomeViewPort
from src.ui.welcome.layout import fit_welcome_window, release_welcome_window
from src.ui.welcome.navigation import get_labels
from src.ui.welcome.navigation_presenter import WelcomeNavigationPresenter
from src.ui.welcome.page_builders import (
    build_done,
    build_hello,
    build_license,
    build_main,
    build_private,
    build_set_workdir,
)
from src.ui.welcome.styles import NAVIGATION_PAD, WelcomeFonts, create_welcome_fonts


PageBuilder = Callable[[WelcomeViewPort], None]


class Welcome(ttk.Frame):
    """Initial setup view using a stable stack of prebuilt pages."""

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
        self.content_wrap_width = max(
            min(self.main_window.winfo_screenwidth() - 80, 640),
            220,
        )
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

        self._page_stack = ttk.Frame(self)
        self._page_stack.pack(
            expand=True,
            fill=BOTH,
            padx=10,
            pady=10,
        )
        self._page_stack.rowconfigure(0, weight=1)
        self._page_stack.columnconfigure(0, weight=1)
        self._page_frames: dict[int, ttk.Frame] = {}
        self._page_takefocus: dict[str, object] = {}
        self.frame = ttk.Frame(self._page_stack)

        self.button_frame = ttk.Frame(self)
        labels = get_labels(self.texts)
        self.back = ttk.Button(
            self.button_frame,
            text=labels.back,
            command=lambda: self.change_page(self.oobe - 1),
        )
        self.back.pack(
            fill=X,
            padx=NAVIGATION_PAD,
            pady=NAVIGATION_PAD,
            side='left',
            expand=True,
        )
        self.next = ttk.Button(
            self.button_frame,
            text=labels.next,
            command=lambda: self.change_page(self.oobe + 1),
        )
        self.next.pack(
            fill=X,
            padx=NAVIGATION_PAD,
            pady=NAVIGATION_PAD,
            side='right',
            expand=True,
        )
        self.button_frame.pack(
            expand=False,
            fill=X,
            padx=NAVIGATION_PAD,
            pady=NAVIGATION_PAD,
            side='bottom',
        )

        self.oobe = self.controller.initial_step()
        self._window_revealed = False
        try:
            self._rebuild_page_frames()
            self._render_page(self.oobe, persist=True)
            fit_welcome_window(self.main_window, self)
            self.main_window.update_idletasks()
            self._reveal_once()
            self.wait_window()
        finally:
            self.actions.set_oobe_active(False)

    def _rebuild_page_frames(self) -> None:
        previous_frames = tuple(self._page_frames.values())
        previous_visible = self._page_frames.get(self.oobe)
        focused = self.main_window.focus_get()
        focus_was_in_replaced_page = any(
            self._is_widget_within(focused, frame) for frame in previous_frames
        )
        rebuilt: dict[int, ttk.Frame] = {}

        for step, builder in self.frames.items():
            frame = ttk.Frame(self._page_stack)
            frame.grid(row=0, column=0, sticky='nsew')
            self.frame = frame
            builder(self)
            apply_native_theme(frame, current_theme_id())
            rebuilt[step] = frame
            if previous_visible is not None:
                previous_visible.tkraise()

        self._page_frames = rebuilt
        self._page_takefocus = {}
        self.frame = rebuilt[self.oobe]
        self.frame.tkraise()
        self._set_active_page_focusability(self.oobe)
        self.main_window.update_idletasks()

        for frame in previous_frames:
            try:
                frame.destroy()
            except TclError:
                continue

        if focus_was_in_replaced_page:
            self.next.focus_set()

    @staticmethod
    def _is_widget_within(widget: tk.Misc | None, ancestor: tk.Misc) -> bool:
        current = widget
        while current is not None:
            if current is ancestor:
                return True
            current = getattr(current, 'master', None)
        return False

    @staticmethod
    def _walk_widget_tree(parent: tk.Misc) -> tuple[tk.Misc, ...]:
        widgets: list[tk.Misc] = []
        pending = list(parent.winfo_children())
        while pending:
            widget = pending.pop()
            widgets.append(widget)
            pending.extend(widget.winfo_children())
        return tuple(widgets)

    def _set_active_page_focusability(self, active_step: int) -> None:
        for step, page in self._page_frames.items():
            enabled = step == active_step
            for widget in self._walk_widget_tree(page):
                widget_path = str(widget)
                try:
                    original = self._page_takefocus.setdefault(
                        widget_path,
                        widget.cget('takefocus'),
                    )
                    widget.configure(
                        **{'takefocus': original if enabled else False}
                    )
                except TclError:
                    # A custom widget may not expose Tk's takefocus option.
                    continue

    def _update_navigation(self) -> None:
        labels = get_labels(self.texts)
        nav_state = WelcomeNavigationPresenter.build_state(
            step=self.oobe,
            frame_count=len(self.frames),
            labels=labels,
        )
        self.back.config(
            text=labels.back,
            state='normal' if nav_state.back_enabled else 'disabled',
        )
        if nav_state.is_last:
            self.next.config(text=nav_state.next_text, command=self.destroy_welcome)
        else:
            self.next.config(
                text=nav_state.next_text,
                command=lambda: self.change_page(self.oobe + 1),
            )

    def _render_page(self, step: int, *, persist: bool) -> None:
        resolved_step = self.controller.persist_step(step) if persist else self.controller.clamp_step(step)
        previous_frame = self.frame
        focused = self.main_window.focus_get()
        move_focus_to_navigation = (
            previous_frame is not self._page_frames[resolved_step]
            and self._is_widget_within(focused, previous_frame)
        )
        self.oobe = resolved_step

        # Every page is built and mapped in the stack before the root is first
        # revealed.  Navigation therefore raises one complete cached surface;
        # it never destroys a visible page or resizes the native window.
        self.frame = self._page_frames[resolved_step]
        self.frame.tkraise()
        self._set_active_page_focusability(resolved_step)
        self._update_navigation()
        if move_focus_to_navigation:
            self.next.focus_set()

    def _reveal_once(self) -> None:
        if self._window_revealed:
            return
        reveal_window_after_layout(
            self.main_window,
            target_alpha=current_window_alpha(),
            focus=True,
        )
        self._window_revealed = True

    def change_page(self, step: int = 0) -> None:
        self._render_page(step, persist=True)

    def apply_selected_language(self) -> None:
        self.actions.apply_language(self.language_var.get())
        with snapshot_window_transition(self.main_window):
            self._rebuild_page_frames()
            self._render_page(self.oobe, persist=False)
            self.main_window.update_idletasks()

    def destroy_welcome(self) -> None:
        self.actions.set_oobe_active(False)
        # Keep the root hidden while bootstrap replaces the wizard with the
        # substantially larger main UI. Bootstrap reveals it after composition.
        self.main_window.withdraw()
        if self.winfo_exists():
            self.destroy()
        release_welcome_window(self.main_window)


__all__ = ['Welcome']
