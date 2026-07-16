from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


class PluginConfigError(ValueError):
    """Raised when a plugin dialog configuration is invalid."""


def _required_mapping(value: object, *, path: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise PluginConfigError(f'Plugin configuration {path} must be an object')
    return value


def _required_text(
    value: object,
    *,
    path: str,
    allow_empty: bool = False,
) -> str:
    if not isinstance(value, str):
        raise PluginConfigError(f'Plugin configuration {path} must be a string')
    text = value.strip()
    if not text and not allow_empty:
        raise PluginConfigError(f'Plugin configuration {path} cannot be empty')
    return text


def _option_text(value: object, *, path: str) -> str:
    if value is None:
        return 'None'
    if isinstance(value, bool):
        return 'True' if value else 'False'
    if isinstance(value, (str, int, float)):
        return str(value)
    raise PluginConfigError(
        f'Plugin configuration {path} must be a scalar value'
    )


@dataclass(frozen=True, slots=True)
class PluginControlConfig:
    control_type: str
    options: tuple[tuple[str, str], ...]

    @classmethod
    def from_mapping(
        cls,
        value: object,
        *,
        path: str,
    ) -> PluginControlConfig:
        mapping = _required_mapping(value, path=path)
        control_type = _required_text(
            mapping.get('type'),
            path=f'{path}.type',
        )
        options = tuple(
            (
                str(key),
                _option_text(option, path=f'{path}.{key}'),
            )
            for key, option in mapping.items()
            if key != 'type'
        )
        return cls(control_type=control_type, options=options)

    def value_for(self, name: str, default: str = 'None') -> str:
        return dict(self.options).get(name, default)


@dataclass(frozen=True, slots=True)
class PluginConfigInfo:
    title: str
    height: str
    width: str
    resize: bool
    assert_unknown_control: bool


@dataclass(frozen=True, slots=True)
class PluginControlGroup:
    name: str
    title: str
    controls: tuple[PluginControlConfig, ...]


@dataclass(frozen=True, slots=True)
class PluginDialogConfig:
    info: PluginConfigInfo
    groups: tuple[PluginControlGroup, ...]


class PluginConfigService:
    def load(self, config_path: str | Path) -> PluginDialogConfig:
        path = Path(config_path)
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
        except OSError as exc:
            raise PluginConfigError(
                f'Unable to read plugin configuration: {path}'
            ) from exc
        except json.JSONDecodeError as exc:
            raise PluginConfigError(
                f'Invalid plugin configuration JSON: {exc}'
            ) from exc

        root = _required_mapping(payload, path='root')
        main = _required_mapping(root.get('main'), path='main')
        raw_info = _required_mapping(main.get('info'), path='main.info')
        for required_key in ('title', 'height', 'weight', 'resize'):
            if required_key not in raw_info:
                raise PluginConfigError(
                    f'Plugin configuration is missing main.info.{required_key}'
                )
        info = PluginConfigInfo(
            title=_required_text(
                raw_info.get('title'),
                path='main.info.title',
            ),
            height=_option_text(
                raw_info.get('height'),
                path='main.info.height',
            ),
            width=_option_text(
                raw_info.get('weight'),
                path='main.info.weight',
            ),
            resize=_option_text(
                raw_info.get('resize'),
                path='main.info.resize',
            ) in {'1', 'True', 'true', 'yes', 'Yes'},
            assert_unknown_control=_option_text(
                raw_info.get('assert', 'False'),
                path='main.info.assert',
            ) in {'1', 'True', 'true', 'yes', 'Yes'},
        )

        groups: list[PluginControlGroup] = []
        for group_name, raw_group in main.items():
            if group_name == 'info':
                continue
            group_path = f'main.{group_name}'
            group = _required_mapping(raw_group, path=group_path)
            title = _required_text(
                group.get('title'),
                path=f'{group_path}.title',
            )
            raw_controls = group.get('controls')
            if not isinstance(raw_controls, list):
                raise PluginConfigError(
                    f'Plugin configuration {group_path}.controls must be an array'
                )
            controls = tuple(
                PluginControlConfig.from_mapping(
                    control,
                    path=f'{group_path}.controls[{index}]',
                )
                for index, control in enumerate(raw_controls)
            )
            groups.append(
                PluginControlGroup(
                    name=str(group_name),
                    title=title,
                    controls=controls,
                )
            )
        return PluginDialogConfig(info=info, groups=tuple(groups))

    @staticmethod
    def execute_command(
        command: str,
        namespace: Mapping[str, object] | None = None,
    ) -> None:
        if not command.strip():
            return
        local_namespace = dict(namespace or {})
        exec(command, {'__builtins__': __builtins__}, local_namespace)


__all__ = [
    'PluginConfigError',
    'PluginConfigInfo',
    'PluginConfigService',
    'PluginControlConfig',
    'PluginControlGroup',
    'PluginDialogConfig',
]
