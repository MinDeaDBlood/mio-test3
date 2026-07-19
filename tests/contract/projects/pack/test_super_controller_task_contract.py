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


from types import SimpleNamespace

from src.app.projects.pack.super_controller import SuperPackController


class _Runner:
    def __init__(self):
        self.calls = []

    def run(self, worker, *args, **kwargs):
        self.calls.append((worker, args, kwargs))
        return True


def test_super_controller_passes_domain_arguments_as_worker_kwargs() -> None:
    window_runner = _Runner()
    host_runner = _Runner()
    manager = SimpleNamespace(current_work_path=lambda: '/project/work/', current_work_output_path=lambda: '/project/output/')
    runtime = SimpleNamespace(
        work_path='/project/output/',
        input_path='/project/input/',
        metadata_path='/project/work/',
        project_manager=manager,
    )
    controller = SuperPackController(runtime=runtime, window_task_runner=window_runner, host_task_runner=host_runner)

    controller.generate_dynamic_list(
        group_name='main',
        size=1024,
        super_type=1,
        part_list=['system'],
        on_error=lambda _error: None,
        on_finally=lambda: None,
    )
    controller.start_pack(
        sparse=True,
        group_name='main',
        size=1024,
        super_type=1,
        part_list=['system'],
        del_=False,
        attrib='readonly',
        block_device_name='super',
        on_success=lambda _result: None,
        on_error=lambda _error: None,
        on_finally=lambda: None,
    )

    generate_kwargs = window_runner.calls[0][2]
    assert generate_kwargs['worker_kwargs']['part_list'] == ['system']
    assert generate_kwargs['worker_kwargs']['work'] == '/project/output/'
    assert generate_kwargs['exclusive'] is True
    pack_kwargs = host_runner.calls[0][2]
    assert pack_kwargs['worker_kwargs'] == {
        'sparse': True,
        'group_name': 'main',
        'size': 1024,
        'super_type': 1,
        'part_list': ['system'],
        'del_': False,
        'attrib': 'readonly',
        'block_device_name': 'super',
        'work': '/project/output/',
        'source_dirs': ['/project/input/'],
        'output_dir': '/project/output/',
        'return_result': True,
    }
    assert pack_kwargs['exclusive'] is True

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
