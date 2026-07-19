from __future__ import annotations

# Direct file execution bootstrap
import sys as _direct_sys
from pathlib import Path as _DirectPath

_DIRECT_PROJECT_ROOT = _DirectPath(__file__).resolve().parent
while _DIRECT_PROJECT_ROOT != _DIRECT_PROJECT_ROOT.parent:
    if (
        (_DIRECT_PROJECT_ROOT / 'src').is_dir()
        and (_DIRECT_PROJECT_ROOT / 'tests').is_dir()
        and (_DIRECT_PROJECT_ROOT / 'scripts').is_dir()
    ):
        break
    _DIRECT_PROJECT_ROOT = _DIRECT_PROJECT_ROOT.parent
else:
    raise RuntimeError(f'Project root was not found for {__file__}')

_direct_root_text = str(_DIRECT_PROJECT_ROOT)
if _direct_root_text not in _direct_sys.path:
    _direct_sys.path.insert(0, _direct_root_text)
if __package__ in {None, ''}:
    _direct_relative = _DirectPath(__file__).resolve().relative_to(
        _DIRECT_PROJECT_ROOT
    ).with_suffix('')
    __package__ = '.'.join(_direct_relative.parts[:-1])

from pathlib import Path

from src.platform import process_restart


def test_build_restart_argv_for_frozen_executable(tmp_path: Path) -> None:
    executable = tmp_path / 'tool.exe'
    executable.touch()

    argv = process_restart.build_restart_argv(
        tool_self=str(executable),
        original_argv=[str(executable), '--project', 'Demo'],
        executable=str(executable),
    )

    assert argv == [str(executable), '--project', 'Demo']


def test_launch_replacement_process_does_not_wait(monkeypatch) -> None:
    calls: list[tuple[list[str], dict[str, str]]] = []

    class FakeProcess:
        pid = 4242

        def wait(self) -> None:
            raise AssertionError('Replacement launch must not wait for process exit')

    def fake_launch_detached(argv, *, env):
        calls.append((argv, env))
        return FakeProcess()

    monkeypatch.setattr(process_restart, 'launch_detached', fake_launch_detached)

    pid = process_restart.launch_replacement_process(
        ['tool.exe', '--project', 'Demo'],
        environment={'MIO_TEST': '1'},
    )

    assert pid == 4242
    assert calls == [
        (
            ['tool.exe', '--project', 'Demo'],
            {'MIO_TEST': '1', 'PYINSTALLER_RESET_ENVIRONMENT': '1'},
        )
    ]


def test_build_restart_environment_does_not_mutate_source() -> None:
    source = {'MIO_TEST': '1'}

    result = process_restart.build_restart_environment(source)

    assert source == {'MIO_TEST': '1'}
    assert result == {
        'MIO_TEST': '1',
        'PYINSTALLER_RESET_ENVIRONMENT': '1',
    }

if __name__ == '__main__':
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
