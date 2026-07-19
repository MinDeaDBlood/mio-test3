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


from pathlib import Path

import pytest

from src.logic.projects.pack.hybrid import (
    HybridPackError,
    HybridPackRequest,
    HybridRomPackService,
)
from src.logic.projects.pack.postinstall import PostInstallConfigRepository, PostInstallEntry


def _template(root: Path) -> Path:
    template = root / 'template'
    script = template / 'META-INF' / 'com' / 'google' / 'android' / 'update-binary'
    script.parent.mkdir(parents=True)
    script.write_text('#!/sbin/sh\n#Other images\n', encoding='utf-8')
    return template


def test_hybrid_pack_moves_images_and_writes_script(tmp_path: Path):
    output = tmp_path / 'output'
    output.mkdir()
    (output / 'system.img').write_bytes(b'raw')
    template = _template(tmp_path)

    service = HybridRomPackService(
        image_type_getter=lambda _path: 'raw',
        sparse_converter=lambda _path: None,
    )
    result = service.pack(
        HybridPackRequest(
            output_dir=output,
            template_dir=template,
            right_device='example_device',
            compression_threshold=1024,
        )
    )

    assert (output / 'images' / 'system.img').read_bytes() == b'raw'
    assert (output / 'bin' / 'right_device').read_text(encoding='gbk') == 'example_device\n'
    script = (output / 'META-INF' / 'com' / 'google' / 'android' / 'update-binary').read_text(encoding='utf-8')
    assert 'right_device="example_device"' in script
    assert 'package_extract_file "images/system.img" "/dev/block/by-name/system"' in script
    assert result.operations[0].image_name == 'system.img'


def test_hybrid_pack_compresses_large_image(tmp_path: Path):
    output = tmp_path / 'output'
    output.mkdir()
    (output / 'vendor.img').write_bytes(b'large')
    template = _template(tmp_path)

    def process_call(command):
        source = Path(command[3])
        target = Path(command[5])
        target.write_bytes(source.read_bytes())
        source.unlink()
        return 0

    result = HybridRomPackService(
        process_call=process_call,
        image_type_getter=lambda _path: 'raw',
    ).pack(
        HybridPackRequest(output, template, 'device', compression_threshold=1)
    )

    assert result.operations[0].compressed is True
    assert (output / 'images' / 'vendor.img.zst').is_file()


def test_hybrid_pack_rejects_negative_threshold(tmp_path: Path):
    output = tmp_path / 'output'
    output.mkdir()
    with pytest.raises(HybridPackError, match='threshold'):
        HybridRomPackService().pack(HybridPackRequest(output, _template(tmp_path), 'device', -1))


def test_postinstall_repository_roundtrip(tmp_path: Path):
    path = tmp_path / 'postinstall_config.txt'
    repository = PostInstallConfigRepository(path)
    repository.save(
        [
            PostInstallEntry(
                partition='system',
                run_postinstall=True,
                postinstall_path='system/bin/otapreopt_script',
                filesystem_type='ext4',
                postinstall_optional=True,
            )
        ]
    )

    loaded = repository.load()
    assert loaded['system'] == PostInstallEntry(
        partition='system',
        run_postinstall=True,
        postinstall_path='system/bin/otapreopt_script',
        filesystem_type='ext4',
        postinstall_optional=True,
    )

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
