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
import zipfile
from pathlib import Path

import pytest

from src.logic.plugins.catalog import PluginCatalogService
from src.logic.plugins.editor import PluginEditorService
from src.logic.plugins.package_reader import PluginPackageError, PluginPackageReader
from src.logic.plugins.runtime import VirtualPluginInfo


def _write_mpk(path: Path, info: str, *, icon: bytes | None = None) -> None:
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('info', info)
        if icon is not None:
            archive.writestr('icon', icon)


def test_plugin_package_reader_returns_plain_metadata(tmp_path: Path):
    package = tmp_path / 'sample.mpk'
    _write_mpk(
        package,
        '[module]\nname=Sample\nversion=1.0\nauthor=Author\ndescribe=Description\n',
        icon=b'icon',
    )

    info = PluginPackageReader().read(package)

    assert info.name == 'Sample'
    assert info.version == '1.0'
    assert info.icon_data == b'icon'


def test_plugin_package_reader_requires_module_section(tmp_path: Path):
    package = tmp_path / 'broken.mpk'
    _write_mpk(package, 'name=Sample\n')

    with pytest.raises(PluginPackageError, match='module section'):
        PluginPackageReader().read(package)


def test_plugin_catalog_reads_models_without_ui(tmp_path: Path):
    module_dir = tmp_path / 'module'
    plugin_dir = module_dir / 'real.plugin'
    plugin_dir.mkdir(parents=True)
    (plugin_dir / 'info.json').write_text(json.dumps({'name': 'Real Plugin'}), encoding='utf-8')
    (plugin_dir / 'icon').write_bytes(b'icon')

    result = PluginCatalogService(
        module_dir=module_dir,
        virtual_plugins={
            'virtual.plugin': VirtualPluginInfo(
                plugin_id='virtual.plugin',
                name='Virtual Plugin',
                author='',
                version='',
                parent='tests',
            )
        },
    ).load()

    assert [item.plugin_id for item in result.items] == ['virtual.plugin', 'real.plugin']
    assert result.items[0].virtual is True
    assert result.items[1].icon_path == plugin_dir / 'icon'
    assert result.issues == ()


def test_plugin_editor_prevents_directory_escape(tmp_path: Path):
    module_dir = tmp_path / 'module'
    module_dir.mkdir()
    outside = tmp_path / 'outside'
    outside.mkdir()

    with pytest.raises(ValueError, match='escapes'):
        PluginEditorService(module_dir=module_dir).prepare_target('../outside', is_virtual=False)


def test_plugin_editor_creates_shell_entrypoint(tmp_path: Path):
    plugin_dir = tmp_path / 'module' / 'sample'
    plugin_dir.mkdir(parents=True)

    target = PluginEditorService(module_dir=tmp_path / 'module').prepare_target('sample', is_virtual=False)

    assert target.filename == 'main.sh'
    assert (plugin_dir / 'main.sh').read_text(encoding='utf-8') == "echo 'MIO-KITCHEN'\n"

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
