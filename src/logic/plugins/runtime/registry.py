# Copyright (C) 2022-2025 The MIO-KITCHEN-SOURCE Project
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License");
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

import inspect
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum


class Entry(Enum):
    main = 0
    before_pack = 1
    packing = 4
    close = 2
    boot = 3


class Type(Enum):
    normal = 0
    virtual = 1
    environ = 2


class PluginRegistrationError(RuntimeError):
    """Raised when a plugin or one of its entry points is not registered."""


class PluginInvocationError(RuntimeError):
    """Raised when supplied plugin arguments do not match its entry point."""


def _virtual_text(
    payload: Mapping[str, object],
    key: str,
    *,
    default: str,
) -> str:
    value = payload.get(key, default)
    if not isinstance(value, str):
        raise PluginRegistrationError(
            f'Virtual plugin field {key!r} must be a string.'
        )
    return value.strip() or default


@dataclass(frozen=True, slots=True)
class VirtualPluginInfo:
    """Validated metadata for an in-process virtual plugin."""

    plugin_id: str
    name: str
    author: str
    version: str
    parent: str

    @classmethod
    def create(
        cls,
        plugin_id: str,
        *,
        payload: Mapping[str, object] | None = None,
        parent: str = 'addon',
    ) -> VirtualPluginInfo:
        normalized_id = plugin_id.strip()
        if not normalized_id:
            raise PluginRegistrationError('Virtual plugin id cannot be empty.')
        values = payload or {}
        payload_id = _virtual_text(values, 'id', default=normalized_id)
        if payload_id != normalized_id:
            raise PluginRegistrationError(
                f'Virtual plugin metadata id {payload_id!r} does not match {normalized_id!r}.'
            )
        return cls(
            plugin_id=normalized_id,
            name=_virtual_text(values, 'name', default=normalized_id),
            author=_virtual_text(values, 'author', default=''),
            version=_virtual_text(values, 'version', default=''),
            parent=_virtual_text(values, 'parent', default=parent),
        )


PluginCallable = Callable[..., object]


class PluginLoader:
    def __init__(self) -> None:
        self.plugins: dict[str, dict[Entry, PluginCallable]] = {}
        self.virtual: dict[str, VirtualPluginInfo] = {}

    def register(
        self,
        id_: str,
        entry: Entry,
        func: PluginCallable | None = None,
        virtual: bool = False,
        virtual_info: Mapping[str, object] | VirtualPluginInfo | None = None,
        parent: str = 'addon',
    ) -> None:
        plugin_id = id_.strip()
        if not plugin_id:
            raise PluginRegistrationError('Plugin id cannot be empty.')
        if func is None or not callable(func):
            raise PluginRegistrationError(
                f"Plugin '{plugin_id}' entry '{entry.name}' must be registered with a callable."
            )
        self.plugins.setdefault(plugin_id, {})[entry] = func
        if virtual:
            if isinstance(virtual_info, VirtualPluginInfo):
                info = virtual_info
                if info.plugin_id != plugin_id:
                    raise PluginRegistrationError(
                        f'Virtual plugin metadata id {info.plugin_id!r} does not match {plugin_id!r}.'
                    )
            else:
                info = VirtualPluginInfo.create(
                    plugin_id,
                    payload=virtual_info,
                    parent=parent,
                )
            self.virtual[plugin_id] = info
        if entry == Entry.boot:
            self.run(plugin_id, entry)

    def is_registered(self, id_: str) -> bool:
        return id_ in self.plugins or id_ in self.virtual

    def _resolve_entry(self, id_: str, entry: Entry) -> PluginCallable:
        plugin_entries = self.plugins.get(id_)
        if plugin_entries is None:
            raise PluginRegistrationError(f"Plugin '{id_}' is not registered.")
        func = plugin_entries.get(entry)
        if func is None:
            raise PluginRegistrationError(
                f"Plugin '{id_}' entry '{entry.name}' is not registered."
            )
        return func

    @staticmethod
    def _invoke_mapped(
        func: PluginCallable,
        mapped_args: Mapping[str, object],
    ) -> object:
        signature = inspect.signature(func)
        positional_args: list[object] = []
        keyword_args: dict[str, object] = {}
        consumed: set[str] = set()
        accepts_extra_keywords = False

        for name, parameter in signature.parameters.items():
            if parameter.kind is inspect.Parameter.VAR_POSITIONAL:
                continue
            if parameter.kind is inspect.Parameter.VAR_KEYWORD:
                accepts_extra_keywords = True
                continue
            if name not in mapped_args:
                if parameter.default is inspect.Parameter.empty:
                    raise PluginInvocationError(
                        f"Required argument '{name}' is missing for plugin entry '{func.__name__}'."
                    )
                continue
            value = mapped_args[name]
            consumed.add(name)
            if parameter.kind is inspect.Parameter.POSITIONAL_ONLY:
                positional_args.append(value)
            else:
                keyword_args[name] = value

        if accepts_extra_keywords:
            keyword_args.update(
                {
                    name: value
                    for name, value in mapped_args.items()
                    if name not in consumed
                }
            )

        try:
            signature.bind(*positional_args, **keyword_args)
        except TypeError as exc:
            raise PluginInvocationError(
                f"Arguments do not match plugin entry '{func.__name__}': {exc}"
            ) from exc
        return func(*positional_args, **keyword_args)

    def run(
        self,
        id_: str,
        entry: Entry,
        mapped_args: Mapping[str, object] | None = None,
        *args: object,
        **kwargs: object,
    ) -> object:
        func = self._resolve_entry(id_, entry)
        if mapped_args is not None:
            if args or kwargs:
                raise PluginInvocationError(
                    'mapped_args cannot be combined with positional or keyword arguments.'
                )
            return self._invoke_mapped(func, mapped_args)
        return func(*args, **kwargs)

    def run_entry(self, entry: Entry) -> None:
        for plugin_id, entries in tuple(self.plugins.items()):
            if entry in entries:
                self.run(plugin_id, entry)


loader = PluginLoader()


__all__ = [
    'Entry',
    'PluginCallable',
    'PluginInvocationError',
    'PluginLoader',
    'PluginRegistrationError',
    'Type',
    'VirtualPluginInfo',
    'loader',
]
