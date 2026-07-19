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

from src.core.imgkit import unpack_image


def test_imgkit_unpack_builds_explicit_metadata_command(tmp_path: Path) -> None:
    source = tmp_path / 'system.img'
    source.write_bytes(b'image')
    calls = []

    def process_call(*, exe, out):
        calls.append((exe, out))
        return 0

    fs_config = tmp_path / 'config' / 'system_fs_config'
    contexts = tmp_path / 'config' / 'system_file_contexts'
    result = unpack_image(
        source,
        tmp_path / 'output',
        fs_config_path=fs_config,
        file_contexts_path=contexts,
        process_call=process_call,
    )

    assert result.fs_config_path == fs_config
    assert result.file_contexts_path == contexts
    command, out = calls[0]
    assert command[:4] == ['imgkit', 'unpack', '-i', str(source)]
    assert '--fs-config-path' in command
    assert '--file-contexts-path' in command
    assert out is False


def test_imgkit_unpack_propagates_nonzero_exit_code(tmp_path: Path) -> None:
    source = tmp_path / 'system.img'
    source.write_bytes(b'image')
    try:
        unpack_image(source, tmp_path / 'output', process_call=lambda **_kwargs: 7)
    except RuntimeError as exc:
        assert 'exit code 7' in str(exc)
    else:
        raise AssertionError('imgkit failure was reported as success')

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
