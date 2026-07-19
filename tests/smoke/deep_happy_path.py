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
import tempfile
from pathlib import Path

from src.core.avb_disabler import process_fstab
from src.core.json_store import JsonEdit
from src.logic.projects.pack.hybrid import HybridPackRequest, HybridRomPackService
from src.logic.projects.pack.postinstall import PostInstallConfigRepository, PostInstallEntry
from src.logic.tools.fstab_patch import load_fstab_partitions, patch_selected_partitions


def _hybrid_pack_round_trip(base: Path) -> None:
    output = base / 'output'
    template = base / 'template'
    output.mkdir()
    (output / 'system.img').write_bytes(b'system-image')
    (output / 'vendor.img').write_bytes(b'vendor-image')
    update_binary = template / 'META-INF' / 'com' / 'google' / 'android' / 'update-binary'
    update_binary.parent.mkdir(parents=True)
    update_binary.write_text('#!/sbin/sh\n#Other images\n', encoding='utf-8')
    (template / 'bin').mkdir(parents=True)

    service = HybridRomPackService()
    result = service.pack(
        HybridPackRequest(
            output_dir=output,
            template_dir=template,
            right_device='demo-device',
            compression_threshold=1024 * 1024,
        )
    )
    assert {operation.image_name for operation in result.operations} == {'system.img', 'vendor.img'}
    assert all(not operation.compressed for operation in result.operations)
    script = (output / 'META-INF' / 'com' / 'google' / 'android' / 'update-binary').read_text(encoding='utf-8')
    assert 'right_device="demo-device"' in script
    assert 'package_extract_file "images/system.img"' in script
    assert (output / 'images' / 'system.img').is_file()


def _postinstall_round_trip(base: Path) -> None:
    repository = PostInstallConfigRepository(base / 'postinstall_config.txt')
    expected = PostInstallEntry(
        partition='system',
        run_postinstall=True,
        postinstall_path='system/bin/otapreopt_script',
        filesystem_type='ext4',
        postinstall_optional=True,
    )
    repository.save([expected])
    assert repository.load() == {'system': expected}


def _fstab_patch_round_trip(base: Path) -> None:
    work = base / 'workspace'
    fstab = work / 'system' / 'etc' / 'fstab.demo'
    fstab.parent.mkdir(parents=True)
    fstab.write_text(
        '/dev/block/system /system ext4 ro,wait,avb=vbmeta,verify\n',
        encoding='utf-8',
    )
    (work / 'config').mkdir(parents=True)
    (work / 'config' / 'parts_info').write_text(
        json.dumps({'system': 'ext4'}),
        encoding='utf-8',
    )

    partitions = load_fstab_partitions(str(work), json_edit_cls=JsonEdit)
    assert len(partitions) == 1
    assert partitions[0].name == 'system'
    assert partitions[0].fs_type == 'ext4'

    count = patch_selected_partitions(
        partitions,
        ['system'],
        patch_file=process_fstab,
    )
    assert count == 1
    patched = fstab.read_text(encoding='utf-8')
    assert 'avb' not in patched
    assert 'verify' not in patched
    assert patched == '/dev/block/system /system ext4 ro,wait\n'


def main() -> None:
    with tempfile.TemporaryDirectory(prefix='mio-deep-smoke-') as td:
        base = Path(td)
        _hybrid_pack_round_trip(base)
        _postinstall_round_trip(base)
        _fstab_patch_round_trip(base)
    print('DEEP_HAPPY_PATH_SMOKE_OK')


if __name__ == '__main__':
    main()
