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

from src.logic.common.service_output import ServiceOutputEvent, build_service_output
from src.logic.projects.boot_images import service as boot_image_service
from src.logic.projects.boot_images.runtime_context import build_runtime_context


def _runtime(tmp_path: Path):
    input_path = tmp_path / 'input'
    unpack_path = tmp_path / 'unpack'
    output_path = tmp_path / 'output'
    input_path.mkdir()
    unpack_path.mkdir()
    output_path.mkdir()
    events: list[ServiceOutputEvent] = []
    runtime = build_runtime_context(
        input_path=str(input_path),
        work_path=str(unpack_path),
        output_path=str(output_path),
        tool_bin=str(tmp_path / 'bin'),
        magisk_not_decompress='0',
        boot_skip_ramdisk='1',
        output=build_service_output(emit=events.append),
    )
    return runtime, events


def test_vendor_boot_unpack_reads_original_from_input_and_writes_folder_to_unpack(tmp_path: Path):
    runtime, _events = _runtime(tmp_path)
    original = Path(runtime.input_path) / 'vendor_boot.img'
    original.write_bytes(b'vendor boot')
    commands = []

    result = boot_image_service.unpack_boot_image(
        name='vendor_boot',
        runtime=runtime,
        call_func=lambda command: commands.append(command) or 0,
    )

    assert result is True
    assert commands[0][:3] == ['magiskboot', 'unpack', '-h']
    assert Path(commands[0][3]) == original
    assert (Path(runtime.work_path) / 'vendor_boot').is_dir()
    assert not (Path(runtime.work_path) / 'vendor_boot.img').exists()


def test_vendor_boot_repack_reads_original_from_input_and_writes_result_to_output(tmp_path: Path):
    runtime, _events = _runtime(tmp_path)
    original = Path(runtime.input_path) / 'vendor_boot.img'
    original.write_bytes(b'vendor boot')
    source = Path(runtime.work_path) / 'vendor_boot'
    source.mkdir()
    commands = []

    def run_recorded_magiskboot(command):
        commands.append(command)
        if command[:2] == ['magiskboot', 'repack']:
            (source / 'new-boot.img').write_bytes(b'new vendor boot')
        return 0

    result = boot_image_service.repack_boot_image(
        name='vendor_boot',
        runtime=runtime,
        call_func=run_recorded_magiskboot,
    )

    assert result is True
    assert commands[0][:2] == ['magiskboot', 'repack']
    assert Path(commands[0][2]) == original
    assert (Path(runtime.output_path) / 'vendor_boot.img').read_bytes() == b'new vendor boot'
    assert not (Path(runtime.work_path) / 'vendor_boot.img').exists()


def test_repack_missing_vendor_boot_names_vendor_boot_not_boot(tmp_path: Path):
    runtime, events = _runtime(tmp_path)
    result = boot_image_service.repack_boot_image(name='vendor_boot', runtime=runtime)

    assert result is None
    [event] = events
    message = event.message
    assert getattr(message, 'code', None) == 'boot_image_origin_missing'
    assert message.params['name'] == 'vendor_boot'
    assert 'vendor_boot.img' in message.render_default()

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
