"""Plugin-domain UI event binding helpers."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from src.app.ui_events import UiCoalescedDrain
from src.logic.plugins.events import PluginStateChangedEvent, plugin_event_bus


class PluginUiEventBinding:
    def __init__(
        self,
        *,
        dispatcher,
        consume: Callable[[Sequence[PluginStateChangedEvent]], None],
        is_alive: Callable[[], bool],
        logger=None,
    ) -> None:
        self._stream = plugin_event_bus.subscribe()
        self._binding = UiCoalescedDrain(
            dispatcher=dispatcher,
            drain=self._stream.drain,
            consume=consume,
            is_alive=is_alive,
            logger=logger,
        )

        def notify_binding() -> None:
            self._binding.notify()

        self._stream.set_on_push(notify_binding)

    def close(self) -> None:
        self._binding.close()
        plugin_event_bus.unsubscribe(self._stream)


__all__ = ["PluginUiEventBinding"]
