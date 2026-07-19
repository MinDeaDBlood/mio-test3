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


import os
from pathlib import Path

from src.logic.common.service_output import build_service_output
from src.logic.projects.pack import filesystem_service


def _recording_output():
    events = []
    return build_service_output(emit=events.append), events


def _metadata(work: Path, name: str = 'system') -> None:
    config = work / 'config'
    config.mkdir(parents=True, exist_ok=True)
    (config / f'{name}_fs_config').write_text(f'/{name} 0 0 0755\n', encoding='utf-8')
    (config / f'{name}_file_contexts').write_text(
        f'/{name}(/.*)? u:object_r:system_file:s0\n',
        encoding='utf-8',
    )


def test_make_f2fs_creates_and_formats_the_output_image(tmp_path, monkeypatch) -> None:
    work = tmp_path / 'work'
    output = tmp_path / 'output'
    (work / 'system').mkdir(parents=True)
    _metadata(work)
    commands = []

    monkeypatch.setattr(filesystem_service, 'call', lambda command, **_kwargs: commands.append(command) or 0)
    service_output, events = _recording_output()

    result = filesystem_service.make_f2fs(
        'system',
        str(work) + os.sep,
        str(output),
        UTC=123,
        output=service_output,
    )

    image = output / 'system.img'
    assert result == 0
    assert image.is_file()
    assert commands[0][0] == 'mkfs.f2fs'
    assert Path(commands[0][1]) == image
    assert Path(commands[1][-1]) == image
    assert not (work / 'system.img').exists()
    assert events


def test_mke2fs_removes_the_actual_output_image_after_e2fsdroid_failure(tmp_path, monkeypatch) -> None:
    work = tmp_path / 'work'
    output = tmp_path / 'output'
    (work / 'system').mkdir(parents=True)
    _metadata(work)
    calls = iter((0, 1))
    monkeypatch.setattr(filesystem_service, 'call', lambda *_args, **_kwargs: next(calls))
    service_output, events = _recording_output()

    result = filesystem_service.mke2fs(
        'system',
        str(work) + os.sep,
        False,
        str(output),
        size=8 * 1024 * 1024,
        UTC=123,
        output=service_output,
    )

    assert result == 1
    assert not (output / 'system_new.img').exists()
    assert events[-1].message.code == 'operation_failed'


def test_packers_stop_before_binary_execution_when_required_metadata_is_missing(tmp_path, monkeypatch) -> None:
    work = tmp_path / 'work'
    output = tmp_path / 'output'
    (work / 'system').mkdir(parents=True)
    calls = []
    monkeypatch.setattr(filesystem_service, 'call', lambda command, **_kwargs: calls.append(command) or 0)

    service_output, events = _recording_output()
    assert filesystem_service.mkerofs('system', 'lz4', str(work), str(output), 0, output=service_output) == 1
    assert filesystem_service.make_f2fs('system', str(work), str(output), output=service_output) == 1
    assert filesystem_service.mke2fs('system', str(work), False, str(output), size=4096, output=service_output) == 1
    assert calls == []
    assert events


def test_mke2fs_rejects_empty_metadata_files(tmp_path: Path, monkeypatch) -> None:
    work = tmp_path / 'work'
    output_dir = tmp_path / 'output'
    (work / 'system').mkdir(parents=True)
    config = work / 'config'
    config.mkdir()
    (config / 'system_fs_config').write_text('', encoding='utf-8')
    (config / 'system_file_contexts').write_text('', encoding='utf-8')
    calls = []
    monkeypatch.setattr(filesystem_service, 'call', lambda command, **kwargs: calls.append(command) or 0)

    result = filesystem_service.mke2fs('system', str(work) + '/', False, str(output_dir))

    assert result == 1
    assert calls == []

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
