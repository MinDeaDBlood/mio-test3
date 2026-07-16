from __future__ import annotations

from dataclasses import dataclass
from queue import SimpleQueue, Empty
from threading import Lock
from typing import Callable, Iterable


@dataclass(frozen=True)
class PluginStateChangedEvent:
    plugin_id: str | None = None
    refresh_manager: bool = True
    refresh_store: bool = True


class PluginEventStream:
    def __init__(self, *, on_push: Callable[[], None] | None = None) -> None:
        self._queue: SimpleQueue[PluginStateChangedEvent] = SimpleQueue()
        self._on_push = on_push


    def set_on_push(self, on_push: Callable[[], None] | None) -> None:
        self._on_push = on_push

    def push(self, event: PluginStateChangedEvent) -> None:
        self._queue.put(event)
        if self._on_push is not None:
            self._on_push()

    def drain(self) -> list[PluginStateChangedEvent]:
        events: list[PluginStateChangedEvent] = []
        while True:
            try:
                events.append(self._queue.get_nowait())
            except Empty:
                return events


class PluginEventBus:
    def __init__(self) -> None:
        self._lock = Lock()
        self._subscribers: set[PluginEventStream] = set()

    def subscribe(self, *, on_push: Callable[[], None] | None = None) -> PluginEventStream:
        stream = PluginEventStream(on_push=on_push)
        with self._lock:
            self._subscribers.add(stream)
        return stream

    def unsubscribe(self, stream: PluginEventStream | None) -> None:
        if stream is None:
            return
        with self._lock:
            self._subscribers.discard(stream)

    def publish(self, event: PluginStateChangedEvent) -> None:
        with self._lock:
            subscribers: Iterable[PluginEventStream] = tuple(self._subscribers)
        for stream in subscribers:
            stream.push(event)


plugin_event_bus = PluginEventBus()
