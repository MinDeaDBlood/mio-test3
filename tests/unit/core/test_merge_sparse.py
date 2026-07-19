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

from src.core.merge_sparse import (
    SparseMergeStatus,
    find_sparse_segments,
    merge_sparse_segments,
)


def test_find_sparse_segments_uses_natural_order(tmp_path: Path):
    for name in ('super.img.10', 'super.img.2', 'super.img.1', 'notes.txt'):
        (tmp_path / name).write_bytes(b'x')

    assert [path.name for path in find_sparse_segments(tmp_path)] == [
        'super.img.1',
        'super.img.2',
        'super.img.10',
    ]


def test_merge_sparse_segments_converts_first_and_appends_remaining(tmp_path: Path):
    source = tmp_path / 'source'
    output = tmp_path / 'output' / 'super.img'
    tools = tmp_path / 'tools'
    source.mkdir()
    tools.mkdir()
    (tools / 'simg2img').write_bytes(b'tool')
    (source / 'super.img.0').write_bytes(b'first')
    (source / 'super.img.1').write_bytes(b'second')
    progress = []

    def process_call(command, *, extra_path, out):
        assert extra_path is False
        assert out is False
        Path(command[2]).write_bytes(b'raw-first')
        return 0

    result = merge_sparse_segments(
        source_directory=source,
        output_path=output,
        tool_bin_path=tools,
        progress_callback=progress.append,
        process_call=process_call,
    )

    assert result.status is SparseMergeStatus.MERGED
    assert output.read_bytes() == b'raw-firstsecond'
    assert progress[-1] == 100
    assert not output.with_name('super.img.part').exists()


def test_merge_sparse_segments_returns_explicit_neutral_states(tmp_path: Path):
    source = tmp_path / 'source'
    tools = tmp_path / 'tools'
    source.mkdir()
    tools.mkdir()
    output = tmp_path / 'super.img'

    no_segments = merge_sparse_segments(
        source_directory=source,
        output_path=output,
        tool_bin_path=tools,
    )
    assert no_segments.status is SparseMergeStatus.NO_SEGMENTS

    output.write_bytes(b'existing')
    exists = merge_sparse_segments(
        source_directory=source,
        output_path=output,
        tool_bin_path=tools,
    )
    assert exists.status is SparseMergeStatus.OUTPUT_EXISTS


def test_merge_sparse_segments_removes_partial_output_after_process_failure(tmp_path: Path):
    source = tmp_path / 'source'
    tools = tmp_path / 'tools'
    source.mkdir()
    tools.mkdir()
    (tools / 'simg2img').write_bytes(b'tool')
    (source / 'super.img.0').write_bytes(b'first')
    output = tmp_path / 'super.img'

    def process_call(command, *, extra_path, out):
        Path(command[2]).write_bytes(b'partial')
        return 7

    with pytest.raises(RuntimeError, match='exit code 7'):
        merge_sparse_segments(
            source_directory=source,
            output_path=output,
            tool_bin_path=tools,
            process_call=process_call,
        )

    assert not output.exists()
    assert not output.with_name('super.img.part').exists()

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
