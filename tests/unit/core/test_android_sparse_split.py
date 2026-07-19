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

from src.core.android_sparse import is_sparse_image, split_raw_image_to_sparse_parts
from src.core.file_types import gettype
from src.core.merge_sparse import SparseMergeStatus, merge_sparse_segments


def test_split_super_sparse_parts_merge_back_byte_exact(tmp_path: Path) -> None:
    block_size = 4096
    raw = bytearray((index * 17) % 256 for index in range(block_size * 11))
    raw[4096:4100] = b'\x67\x44\x6c\x61'
    source = tmp_path / 'super.img'
    source.write_bytes(raw)
    assert gettype(str(source)) == 'super'

    split = split_raw_image_to_sparse_parts(
        source,
        tmp_path / 'parts',
        part_count=4,
        block_size=block_size,
    )
    assert len(split.output_paths) == 4
    assert all(is_sparse_image(path) for path in split.output_paths)

    merged = tmp_path / 'merged.img'
    result = merge_sparse_segments(
        source_directory=tmp_path / 'parts',
        output_path=merged,
        tool_bin_path=tmp_path / 'unused-tools',
    )
    assert result.status is SparseMergeStatus.MERGED
    assert merged.read_bytes() == bytes(raw)
    assert gettype(str(merged)) == 'super'

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
