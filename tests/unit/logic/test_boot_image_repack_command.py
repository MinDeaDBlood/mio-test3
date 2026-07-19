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


import shlex
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, '.')

from src.logic.projects.boot_images import service as boot_image_service


class _FakeOutput:
    def __init__(self):
        self.logs = []

    def log(self, message):
        self.logs.append(message)


def _runtime(tmp_path: Path):
    input_path = tmp_path / 'input'
    input_path.mkdir()
    output_path = tmp_path / 'out'
    output_path.mkdir()
    return SimpleNamespace(
        input_path=str(input_path),
        work_path=str(tmp_path),
        output_path=str(output_path),
        tool_bin='G:/Disk C/mio/bin/Windows/AMD64',
        boot_skip_ramdisk='0',
        output=_FakeOutput(),
    )


def test_repack_boot_quotes_cpio_path_for_busybox_ash_when_tool_path_has_spaces(tmp_path: Path):
    source = tmp_path / 'boot'
    (source / 'ramdisk').mkdir(parents=True)
    (source / 'comp').write_text('unknown', encoding='utf-8')
    boot = tmp_path / 'boot.img'
    boot.write_bytes(b'boot')
    cpio_path = r'G:\Disk C\mio\bin\Windows\AMD64\cpio.exe'
    expected = shlex.quote(cpio_path.replace('\\', '/'))
    commands = []

    result = boot_image_service.repack_boot_image(
        runtime=_runtime(tmp_path),
        source=str(source),
        boot=str(boot),
        call_func=lambda command: commands.append(command) or 1,
        findfile_func=lambda _name, _root: cpio_path,
    )

    assert result == 1
    assert commands == [[
        'busybox',
        'ash',
        '-c',
        f'find | sed 1d | {expected} -H newc -R 0:0 -o -F ../ramdisk-new.cpio',
    ]]


def test_repack_boot_stops_immediately_when_ramdisk_cpio_creation_fails(tmp_path: Path):
    source = tmp_path / 'boot'
    (source / 'ramdisk').mkdir(parents=True)
    (source / 'comp').write_text('unknown', encoding='utf-8')
    boot = tmp_path / 'boot.img'
    boot.write_bytes(b'boot')
    runtime = _runtime(tmp_path)
    commands = []

    result = boot_image_service.repack_boot_image(
        runtime=runtime,
        source=str(source),
        boot=str(boot),
        call_func=lambda command: commands.append(command) or 1,
        findfile_func=lambda _name, _root: 'G:/Disk C/mio/bin/Windows/AMD64/cpio.exe',
    )

    assert result == 1
    assert len(commands) == 1
    assert runtime.output.logs == ['Failed to repack ramdisk.']

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
