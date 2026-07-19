from __future__ import annotations

# Direct file execution bootstrap
import sys as _direct_sys
from pathlib import Path as _DirectPath

_DIRECT_PROJECT_ROOT = _DirectPath(__file__).resolve().parent
while _DIRECT_PROJECT_ROOT != _DIRECT_PROJECT_ROOT.parent:
    if (
        (_DIRECT_PROJECT_ROOT / "src").is_dir()
        and (_DIRECT_PROJECT_ROOT / "tests").is_dir()
        and (_DIRECT_PROJECT_ROOT / "scripts").is_dir()
    ):
        break
    _DIRECT_PROJECT_ROOT = _DIRECT_PROJECT_ROOT.parent
else:
    raise RuntimeError(f"Project root was not found for {__file__}")

_direct_root_text = str(_DIRECT_PROJECT_ROOT)
if _direct_root_text not in _direct_sys.path:
    _direct_sys.path.insert(0, _direct_root_text)
if __package__ in {None, ""}:
    _direct_relative = _DirectPath(__file__).resolve().relative_to(
        _DIRECT_PROJECT_ROOT
    ).with_suffix("")
    __package__ = ".".join(_direct_relative.parts[:-1])


import json
from pathlib import Path

import pytest

from src.logic.plugins.config import PluginConfigError, PluginConfigService
from src.logic.plugins.runtime import (
    Entry,
    PluginLoader,
    PluginRegistrationError,
    VirtualPluginInfo,
)


def test_virtual_plugin_metadata_is_validated_at_registration() -> None:
    loader = PluginLoader()
    loader.register(
        'virtual.demo',
        Entry.main,
        lambda value=None: value,
        virtual=True,
        virtual_info={
            'id': 'virtual.demo',
            'name': 'Virtual Demo',
            'author': 'MIO',
            'version': '1.0',
            'parent': 'tests',
        },
    )

    assert loader.virtual['virtual.demo'] == VirtualPluginInfo(
        plugin_id='virtual.demo',
        name='Virtual Demo',
        author='MIO',
        version='1.0',
        parent='tests',
    )
    assert loader.run(
        'virtual.demo',
        Entry.main,
        mapped_args={'value': 'ok'},
    ) == 'ok'

    with pytest.raises(PluginRegistrationError, match='does not match'):
        loader.register(
            'virtual.demo',
            Entry.close,
            lambda: None,
            virtual=True,
            virtual_info={'id': 'another.id'},
        )

    with pytest.raises(PluginRegistrationError, match='must be a string'):
        loader.register(
            'broken.virtual',
            Entry.main,
            lambda: None,
            virtual=True,
            virtual_info={'name': 7},
        )


def test_plugin_dialog_config_is_parsed_into_immutable_models(tmp_path: Path) -> None:
    config_path = tmp_path / 'main.json'
    config_path.write_text(
        json.dumps(
            {
                'main': {
                    'info': {
                        'title': 'Demo',
                        'height': 320,
                        'weight': '480',
                        'resize': '1',
                        'assert': False,
                    },
                    'general': {
                        'title': 'General',
                        'controls': [
                            {
                                'type': 'input',
                                'set': 'name',
                                'text': 'Plugin name',
                            },
                            {
                                'type': 'checkbutton',
                                'set': 'enabled',
                                'text': None,
                            },
                        ],
                    },
                }
            }
        ),
        encoding='utf-8',
    )

    config = PluginConfigService().load(config_path)

    assert config.info.title == 'Demo'
    assert config.info.height == '320'
    assert config.info.width == '480'
    assert config.info.resize is True
    assert config.groups[0].name == 'general'
    assert config.groups[0].controls[0].control_type == 'input'
    assert config.groups[0].controls[0].value_for('set') == 'name'
    assert config.groups[0].controls[1].value_for('text') == 'None'


def test_plugin_dialog_config_rejects_nested_untyped_control_values(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / 'bad.json'
    config_path.write_text(
        json.dumps(
            {
                'main': {
                    'info': {
                        'title': 'Demo',
                        'height': '320',
                        'weight': '480',
                        'resize': '1',
                    },
                    'general': {
                        'title': 'General',
                        'controls': [
                            {'type': 'input', 'text': {'nested': True}}
                        ],
                    },
                }
            }
        ),
        encoding='utf-8',
    )

    with pytest.raises(PluginConfigError, match='must be a scalar value'):
        PluginConfigService().load(config_path)

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
