
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

from src.logic.projects.unpack.workflow.compressed_dat import unpack_compressed_dat
from src.logic.projects.unpack.zst.service import scan_candidates


class Output:
    def __init__(self) -> None:
        self.logs: list[str] = []

    def log(self, value) -> None:
        self.logs.append(str(value))


def test_zst_candidate_strips_img_suffix(tmp_path: Path) -> None:
    (tmp_path / 'system.img.zst').write_bytes(b'zstd')

    candidates = scan_candidates(str(tmp_path))

    assert [candidate.name for candidate in candidates] == ['system']


def test_zst_is_decompressed_to_partition_image_and_continues(tmp_path: Path) -> None:
    source = tmp_path / 'system.img.zst'
    source.write_bytes(b'zstd')
    calls = []

    def fake_call(command, **_kwargs):
        calls.append(command)
        (tmp_path / 'unpack' / 'system.img').write_bytes(b'raw-image')
        return 0

    work = tmp_path / 'unpack'
    work.mkdir()

    result = unpack_compressed_dat(
        str(tmp_path),
        str(work),
        'system',
        {},
        output=Output(),
        call_func=fake_call,
    )

    assert result is False
    assert calls == [[
        'zstd', '-d', str(source), '-o', str(work / 'system.img')
    ]]
    assert source.exists()
    assert (work / 'system.img').read_bytes() == b'raw-image'

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
