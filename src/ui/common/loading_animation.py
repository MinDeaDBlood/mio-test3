from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from PIL.Image import Image
    from PIL.ImageTk import PhotoImage


class AnimationLabelProtocol(Protocol):
    def pack(self, **kwargs: object) -> object: ...
    def pack_forget(self) -> object: ...
    def configure(self, **kwargs: object) -> object: ...
    def after(self, delay_ms: int, callback: object, *args: object) -> str: ...
    def after_cancel(self, callback_id: str) -> None: ...


class AnimationHostProtocol(Protocol):
    gif_label: AnimationLabelProtocol


class LoadingAnimation:
    """Render and stop the loading GIF in the Tk main window."""

    def __init__(self, master: AnimationHostProtocol | None = None) -> None:
        self.master = master
        self.frames: list['PhotoImage'] = []
        self._scheduled_callback: str | None = None
        self._stopped = True

    def start(self, frame_index: int = 0) -> int:
        if self._stopped and frame_index != 0:
            return 0
        self._stopped = False
        if self.master is None:
            logging.warning('Loading animation has no host window.')
            return 1
        if not self.frames:
            logging.warning('Loading animation frames are not initialized.')
            return 1
        try:
            self.master.gif_label.pack(padx=10, pady=10)
            frame = self.frames[frame_index]
            self.master.gif_label.configure(image=frame)
            next_index = (frame_index + 1) % len(self.frames)
            self._scheduled_callback = self.master.gif_label.after(
                30,
                self.start,
                next_index,
            )
        except RuntimeError:
            return 1
        return 0

    def stop(self) -> None:
        if self.master is None:
            self._scheduled_callback = None
            self._stopped = True
            return
        callback_id = self._scheduled_callback
        self._scheduled_callback = None
        if callback_id is not None:
            try:
                self.master.gif_label.after_cancel(callback_id)
            except Exception:
                logging.exception('Error stopping loading animation')
        try:
            self.master.gif_label.pack_forget()
        except Exception:
            logging.exception('Error hiding loading animation')
        self._stopped = True

    def initialize(self) -> None:
        self.start()
        self.stop()

    def load_gif(self, gif: 'Image') -> None:
        from PIL.ImageTk import PhotoImage

        self.frames.clear()
        while True:
            self.frames.append(PhotoImage(gif))
            try:
                gif.seek(len(self.frames))
            except EOFError:
                break


__all__ = [
    'AnimationHostProtocol',
    'AnimationLabelProtocol',
    'LoadingAnimation',
]
