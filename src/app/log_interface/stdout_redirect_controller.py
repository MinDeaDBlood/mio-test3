from __future__ import annotations

from queue import SimpleQueue, Empty
from typing import Callable


class StdoutRedirectController:
    def __init__(self, *, error_mode: bool = False, logger=None, on_chunk: Callable[[], bool] | None = None):
        self.error_mode = error_mode
        self.logger = logger
        self.data = ''
        self.error_info = ''
        self.pending_error_popup = False
        self.queue = SimpleQueue()
        self.on_chunk = on_chunk

    def write(self, value) -> None:
        if value is None:
            return
        text = str(value)
        if not text:
            return
        self.data += text
        self.queue.put(text)
        if self.error_mode:
            self.error_info += text
            if self.logger:
                try:
                    self.logger.error(text.rstrip())
                except Exception:
                    ...
        elif self.logger:
            try:
                self.logger.debug(text.rstrip())
            except Exception:
                ...
        if self.on_chunk is not None:
            self.on_chunk()

    def drain_chunks(self) -> list[str]:
        chunks: list[str] = []
        while True:
            try:
                chunks.append(self.queue.get_nowait())
            except Empty:
                break
        return chunks

    def request_error_popup(self) -> bool:
        if self.error_mode and self.error_info:
            self.pending_error_popup = True
            return True
        return False

    def consume_error_popup(self) -> str:
        if not self.pending_error_popup:
            return ''
        self.pending_error_popup = False
        return self.error_info
