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
from types import SimpleNamespace

from src.app.tools.allow_selinux_audit_controller import SelinuxAuditAllowController
from src.app.tools.merge_qualcomm_controller import MergeQualcommController
from src.app.tools.merge_super_controller import MergeSuperController
from src.app.tools.mtk_port_controller import MtkPortController
from src.app.tools.split_super_controller import SplitSuperController


class RecordingRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[object, tuple[object, ...], dict[str, object]]] = []

    def run(self, worker, *args, **kwargs):
        self.calls.append((worker, args, kwargs))
        return None


class ImmediateDispatcher:
    def dispatch(self, callback, *args):
        callback(*args)
        return True


def test_split_super_controller_builds_request_and_routes_progress(monkeypatch, tmp_path: Path) -> None:
    captured = {}
    progress_values: list[int] = []

    def fake_execute(request, *, progress_callback):
        captured['request'] = request
        progress_callback(37)
        return 'done'

    monkeypatch.setattr('src.app.tools.split_super_controller.execute_split_super', fake_execute)
    runner = RecordingRunner()
    controller = SplitSuperController(task_runner=runner, dispatcher=ImmediateDispatcher())

    controller.start(
        input_path=str(tmp_path / 'super.img'),
        output_directory=str(tmp_path / 'parts'),
        part_count=4,
        block_size=4096,
        suffix_format='.%03d',
        keep_existing=True,
        on_progress=progress_values.append,
        on_success=lambda _result: None,
        on_error=lambda _error: None,
        on_finally=lambda: None,
    )

    worker, args, kwargs = runner.calls[0]
    assert args == ()
    assert kwargs['exclusive'] is True
    assert worker() == 'done'
    request = captured['request']
    assert request.input_path == str(tmp_path / 'super.img')
    assert request.output_directory == str(tmp_path / 'parts')
    assert request.part_count == 4
    assert request.block_size == 4096
    assert request.suffix_format == '.%03d'
    assert request.keep_existing is True
    assert progress_values == [37]


def test_merge_super_controller_builds_request_inside_app_boundary() -> None:
    captured = {}

    class Service:
        def execute(self, request, *, progress_callback):
            captured['request'] = request
            progress_callback(50)
            return 'merged'

    runner = RecordingRunner()
    progress_values: list[int] = []
    controller = MergeSuperController(
        service=Service(),
        task_runner=runner,
        dispatcher=ImmediateDispatcher(),
    )

    controller.start(
        output_name='super-new.img',
        delete_source=True,
        on_progress=progress_values.append,
        on_success=lambda _result: None,
        on_error=lambda _error: None,
        on_finally=lambda: None,
    )

    worker, args, kwargs = runner.calls[0]
    assert args == ()
    assert kwargs['exclusive'] is True
    assert worker() == 'merged'
    request = captured['request']
    assert request.output_name == 'super-new.img'
    assert request.delete_source is True
    assert progress_values == [50]


def test_mtk_controller_builds_immutable_request_before_scheduling(tmp_path: Path) -> None:
    runner = RecordingRunner()
    service = SimpleNamespace(execute=lambda _request: None, profiles=lambda: ())
    controller = MtkPortController(service=service, task_runner=runner)
    flags = {'port_boot': True, 'port_system': False}

    controller.start(
        profile_name='mt6893',
        boot_image=tmp_path / 'boot.img',
        system_image=tmp_path / 'system.img',
        port_rom=tmp_path / 'port.zip',
        enabled_flags=flags,
        output_as_image=True,
        patch_magisk=False,
        magisk_apk=None,
        target_arch='arm64-v8a',
        on_success=lambda _result: None,
        on_error=lambda _error: None,
        on_finally=lambda: None,
    )
    flags['port_boot'] = False

    worker, args, kwargs = runner.calls[0]
    assert worker is service.execute
    assert kwargs['exclusive'] is True
    request = args[0]
    assert request.profile_name == 'mt6893'
    assert request.boot_image == tmp_path / 'boot.img'
    assert request.system_image == tmp_path / 'system.img'
    assert request.port_rom == tmp_path / 'port.zip'
    assert request.enabled_flags == {'port_boot': True, 'port_system': False}
    assert request.output_as_image is True
    assert request.target_arch == 'arm64-v8a'


def test_selinux_controller_validates_fields_and_schedules_domain_request(tmp_path: Path) -> None:
    log_path = tmp_path / 'audit.log'
    log_path.write_text('avc: denied', encoding='utf-8')
    output_dir = tmp_path / 'output'
    output_dir.mkdir()
    runner = RecordingRunner()
    controller = SelinuxAuditAllowController(task_runner=runner)

    assert controller.validate(log_path='', output_dir=str(output_dir)) == 'log_path_required'
    assert controller.validate(log_path=str(log_path), output_dir=str(output_dir)) is None
    controller.start(
        log_path=f'  {log_path}  ',
        output_dir=f'  {output_dir}  ',
        on_success=lambda _result: None,
        on_error=lambda _error: None,
    )

    _worker, args, _kwargs = runner.calls[0]
    request = args[0]
    assert request.log_path == str(log_path)
    assert request.output_dir == str(output_dir)


def test_qualcomm_controller_validates_fields_and_schedules_domain_request(tmp_path: Path) -> None:
    xml_path = tmp_path / 'rawprogram0.xml'
    xml_path.write_text('<data/>', encoding='utf-8')
    runner = RecordingRunner()
    controller = MergeQualcommController(task_runner=runner)

    assert controller.validate(rawprogram_xml='', partition_name='system', output_path=str(tmp_path)) == 'rawprogram_not_found'
    assert controller.validate(
        rawprogram_xml=str(xml_path),
        partition_name='system',
        output_path=str(tmp_path / 'output'),
    ) is None
    controller.start(
        rawprogram_xml=f'  {xml_path}  ',
        partition_name='  system  ',
        output_path=f'  {tmp_path / "output"}  ',
        on_success=lambda _result: None,
        on_error=lambda _error: None,
    )

    _worker, args, kwargs = runner.calls[0]
    assert kwargs['exclusive'] is True
    request = args[0]
    assert request.rawprogram_xml == str(xml_path)
    assert request.partition_name == 'system'
    assert request.output_path == str(tmp_path / 'output')

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
