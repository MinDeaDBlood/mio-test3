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


from io import StringIO
from pathlib import Path
from zipfile import ZipFile

import pytest

from src.core.mtk_port import files as mtk_files
from src.core.mtk_port.files import (
    BootImageWorkspace,
    PropertyFile,
    UnsafeArchiveMemberError,
    UpdaterScript,
    safe_extract_zip,
)


def test_safe_extract_zip_extracts_regular_members(tmp_path: Path) -> None:
    archive_path = tmp_path / 'rom.zip'
    with ZipFile(archive_path, 'w') as archive:
        archive.writestr('system/build.prop', 'ro.product.name=test\n')

    destination = tmp_path / 'rom'
    with ZipFile(archive_path) as archive:
        safe_extract_zip(archive, destination)

    assert (destination / 'system' / 'build.prop').read_text(encoding='utf-8') == 'ro.product.name=test\n'


@pytest.mark.parametrize('member_name', ['../escape.txt', '/absolute.txt', 'C:\\escape.txt', '..\\escape.txt'])
def test_safe_extract_zip_rejects_paths_outside_destination(tmp_path: Path, member_name: str) -> None:
    archive_path = tmp_path / 'unsafe.zip'
    with ZipFile(archive_path, 'w') as archive:
        archive.writestr(member_name, 'blocked')

    destination = tmp_path / 'rom'
    with ZipFile(archive_path) as archive:
        with pytest.raises(UnsafeArchiveMemberError):
            safe_extract_zip(archive, destination)

    assert not (tmp_path / 'escape.txt').exists()


def test_property_file_saves_successful_changes_atomically(tmp_path: Path) -> None:
    path = tmp_path / 'build.prop'
    path.write_bytes(b'ro.product.name=old\n')

    with PropertyFile(path) as properties:
        properties.set('ro.product.name', 'new')
        properties.set('ro.debuggable', 1)

    assert path.read_bytes() == b'ro.product.name=new\nro.debuggable=1\n'
    assert not list(tmp_path.glob('.build.prop.*.tmp'))


def test_property_file_does_not_commit_after_exception(tmp_path: Path) -> None:
    path = tmp_path / 'build.prop'
    original = 'ro.product.name=stable\n'
    path.write_text(original, encoding='utf-8')

    with pytest.raises(RuntimeError):
        with PropertyFile(path) as properties:
            properties.set('ro.product.name', 'partial')
            raise RuntimeError('operation failed')

    assert path.read_text(encoding='utf-8') == original


def test_updater_script_uses_configured_partition_paths() -> None:
    source = StringIO('set_metadata("/system/bin/sh", "uid", 0, "gid", 2000, "mode", 0755);')
    generated = UpdaterScript(source).generate(
        'author',
        '1.0',
        {
            'system': '/dev/block/by-name/system',
            'boot': '/dev/block/by-name/boot',
        },
    )

    assert generated is not None
    assert '/dev/block/by-name/system' in generated
    assert '/dev/block/by-name/boot' in generated
    assert '/dev/block/mmcblk0p4' not in generated


def test_boot_workspace_reads_named_fields_independent_of_order(tmp_path: Path, monkeypatch) -> None:
    boot_path = tmp_path / 'boot.img'
    boot_path.write_bytes(b'boot')
    (tmp_path / 'bootinfo.txt').write_text(
        'cmdline:console=null androidboot.hardware=test\n'
        'padding_size:0x800\n'
        'page_size:0x1000\n'
        'base:0x10000000\n',
        encoding='ascii',
    )
    calls: list[tuple[object, ...]] = []
    monkeypatch.setattr(mtk_files, 'repack_bootimg', lambda *args: calls.append(args))

    BootImageWorkspace(boot_path).repack()

    assert calls == [
        ('0x10000000', 'console=null androidboot.hardware=test', '0x1000', '0x800', None),
    ]


def test_boot_workspace_rejects_incomplete_boot_info(tmp_path: Path) -> None:
    boot_path = tmp_path / 'boot.img'
    boot_path.write_bytes(b'boot')
    (tmp_path / 'bootinfo.txt').write_text('base:0x10000000\n', encoding='ascii')

    with pytest.raises(ValueError, match='missing fields'):
        BootImageWorkspace(boot_path).repack()

def test_compress_zip_uses_posix_member_paths(tmp_path: Path) -> None:
    source = tmp_path / 'source'
    nested = source / 'system' / 'bin'
    nested.mkdir(parents=True)
    (nested / 'tool').write_bytes(b'tool')
    archive_path = tmp_path / 'rom.zip'

    mtk_files.compress_zip(archive_path, source)

    with ZipFile(archive_path) as archive:
        assert archive.namelist() == ['system/bin/tool']


if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
